# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'ModelDescription.layer'
        db.delete_column(u'dynamic_modeldescription', 'layer_id')

        # Adding field 'ModelDescription.layer_type'
        db.add_column(u'dynamic_modeldescription', 'layer_type',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['layers.LayerType'], unique=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'ModelDescription.layer'
        db.add_column(u'dynamic_modeldescription', 'layer',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['layers.Layer'], unique=True, null=True, blank=True),
                      keep_default=False)

        # Deleting field 'ModelDescription.layer_type'
        db.delete_column(u'dynamic_modeldescription', 'layer_type_id')


    models = {
        u'dynamic.field': {
            'Meta': {'unique_together': "((u'model', u'name'),)", 'object_name': 'Field'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'fields'", 'to': u"orm['dynamic.ModelDescription']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'original_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'dynamic.modeldescription': {
            'Meta': {'object_name': 'ModelDescription'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layer_type': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['layers.LayerType']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'dynamic.setting': {
            'Meta': {'unique_together': "((u'field', u'name'),)", 'object_name': 'Setting'},
            'field': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'settings'", 'to': u"orm['dynamic.Field']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'layers.layertype': {
            'Meta': {'object_name': 'LayerType'},
            'calculated_abstract': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'calculated_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'default_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['layers.Style']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'fill_metadata': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'geometry_type': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'show_category': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'table_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        u'layers.style': {
            'Meta': {'object_name': 'Style'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'sld_body': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'sld_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'sld_url': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True'}),
            'sld_version': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['dynamic']