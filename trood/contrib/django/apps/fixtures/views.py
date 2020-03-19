from django.core.management.color import no_style
from django.core.serializers.python import Deserializer
from django.db import transaction, connections, router, DatabaseError, IntegrityError, DEFAULT_DB_ALIAS
from rest_framework import viewsets, status
from rest_framework.response import Response


class TroodFixturesViewSet(viewsets.ViewSet):

    def create(self, request):
        objects_in_fixture = 0
        loaded_objects_count = 0
        models = set()

        fixture = request.data.get('fixture')

        if fixture:
            with transaction.atomic():
                connection = connections[DEFAULT_DB_ALIAS]

                with connection.constraint_checks_disabled():
                    objects = Deserializer(fixture, ignorenonexistent=True, handle_forward_references=True)
                    objs_with_deferred_fields = []

                    for obj in objects:
                        objects_in_fixture += 1
                        if router.allow_migrate_model(DEFAULT_DB_ALIAS, obj.object.__class__):
                            loaded_objects_count += 1
                            models.add(obj.object.__class__)
                            try:
                                obj.save()
                            # psycopg2 raises ValueError if data contains NUL chars.
                            except (DatabaseError, IntegrityError, ValueError) as e:
                                e.args = ("Could not load %(app_label)s.%(object_name)s(pk=%(pk)s): %(error_msg)s" % {
                                    'app_label': obj.object._meta.app_label,
                                    'object_name': obj.object._meta.object_name,
                                    'pk': obj.object.pk,
                                    'error_msg': e,
                                },)
                                raise
                        if obj.deferred_fields:
                            objs_with_deferred_fields.append(obj)

                    for obj in objs_with_deferred_fields:
                        obj.save_deferred_fields()

                if loaded_objects_count > 0:
                    sequence_sql = connection.ops.sequence_reset_sql(no_style(), models)
                    if sequence_sql:
                        with connection.cursor() as cursor:
                            for line in sequence_sql:
                                cursor.execute(line)
                # Close the DB connection -- unless we're still in a transaction. This
                # is required as a workaround for an edge case in MySQL: if the same
                # connection is used to create tables, load data, and query, the query
                # can return incorrect results. See Django #7572, MySQL #37735.
            if transaction.get_autocommit():
                connections[DEFAULT_DB_ALIAS].close()

        return Response({"objects_loaded": loaded_objects_count}, status=status.HTTP_200_OK)
