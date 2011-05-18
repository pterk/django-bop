from django.core.management import sql
from django.core.management.color import no_style
from django.db import connection


STYLE = no_style()


class TableManager(object):
    """ Create and drop tables/models 'on the fly' 

    Based on: http://djangosnippets.org/snippets/1044/

    Note that models must use an existing app_label.

    class Thing(models.Model):
        afield = models.CharField(max_length=255)

        class Meta:
            app_label = 'my_app'
    """

    def __init__(self):
        self.cursor = connection.cursor()
        self.table_names = connection.introspection.get_table_list(self.cursor)

    def execute(self, statements):
        for statement in statements:
            self.cursor.execute(statement)

    def model_exists(self, model):
        return connection.introspection.table_name_converter(model._meta.db_table) in self.table_names

    def create_table(self, *models):
        """ Create all tables for the given models """
        for model in models:
            if self.model_exists(model):
                continue
            self.execute(connection.creation.sql_create_model(model, STYLE)[0])
            self.execute(connection.creation.sql_indexes_for_model(model, STYLE))
            self.execute(sql.custom_sql_for_model(model, STYLE, connection))

    def drop_table(self, *models):
        """ Drops table(s) for the given models

        See django.core.management.sql 
        """
        output = []
        to_delete = set()
        references_to_delete = {}
        for model in models:
            if self.cursor and self.model_exists(model):
                # The table exists, so it needs to be dropped
                opts = model._meta
                for f in opts.local_fields:
                    if f.rel and f.rel.to not in to_delete:
                        references_to_delete.setdefault(f.rel.to, []).append( (model, f) )

                to_delete.add(model)

        for model in models:
            if self.model_exists(model):
                output.extend(connection.creation.sql_destroy_model(model, references_to_delete, STYLE))

        self.execute(output[::-1])
