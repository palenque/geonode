# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Style'
        db.create_table(u'layers_style', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('sld_title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('sld_body', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('sld_version', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True)),
            ('sld_url', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True)),
            ('workspace', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'layers', ['Style'])

        # Adding model 'Layer'
        db.create_table(u'layers_layer', (
            (u'resourcebase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['base.ResourceBase'], unique=True, primary_key=True)),
            ('title_en', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('title_es', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('abstract_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('abstract_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('purpose_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('purpose_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('constraints_other_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('constraints_other_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('supplemental_information_en', self.gf('django.db.models.fields.TextField')(default=u'No information provided', null=True, blank=True)),
            ('supplemental_information_es', self.gf('django.db.models.fields.TextField')(default=u'No information provided', null=True, blank=True)),
            ('distribution_description_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('distribution_description_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('data_quality_statement_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('data_quality_statement_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('workspace', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('store', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('storeType', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('typename', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('default_style', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='layer_default_style', null=True, to=orm['layers.Style'])),
            ('charset', self.gf('django.db.models.fields.CharField')(default='UTF-8', max_length=255)),
            ('upload_session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.UploadSession'], null=True, blank=True)),
            ('service', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='layer_set', null=True, to=orm['services.Service'])),
        ))
        db.send_create_signal(u'layers', ['Layer'])

        # Adding M2M table for field styles on 'Layer'
        m2m_table_name = db.shorten_name(u'layers_layer_styles')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('layer', models.ForeignKey(orm[u'layers.layer'], null=False)),
            ('style', models.ForeignKey(orm[u'layers.style'], null=False))
        ))
        db.create_unique(m2m_table_name, ['layer_id', 'style_id'])

        # Adding model 'UploadSession'
        db.create_table(u'layers_uploadsession', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['people.Profile'])),
            ('processed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('error', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('traceback', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'layers', ['UploadSession'])

        # Adding model 'LayerFile'
        db.create_table(u'layers_layerfile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('upload_session', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['layers.UploadSession'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('base', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=255)),
        ))
        db.send_create_signal(u'layers', ['LayerFile'])

        # Adding model 'Attribute'
        db.create_table(u'layers_attribute', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('layer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attribute_set', to=orm['layers.Layer'])),
            ('attribute', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('attribute_label', self.gf('django.db.models.fields.CharField')(max_length=255, null=True)),
            ('attribute_type', self.gf('django.db.models.fields.CharField')(default='xsd:string', max_length=50)),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('display_order', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('count', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('min', self.gf('django.db.models.fields.CharField')(default='NA', max_length=255, null=True)),
            ('max', self.gf('django.db.models.fields.CharField')(default='NA', max_length=255, null=True)),
            ('average', self.gf('django.db.models.fields.CharField')(default='NA', max_length=255, null=True)),
            ('median', self.gf('django.db.models.fields.CharField')(default='NA', max_length=255, null=True)),
            ('stddev', self.gf('django.db.models.fields.CharField')(default='NA', max_length=255, null=True)),
            ('sum', self.gf('django.db.models.fields.CharField')(default='NA', max_length=255, null=True)),
            ('unique_values', self.gf('django.db.models.fields.TextField')(default='NA', null=True, blank=True)),
            ('last_stats_updated', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal(u'layers', ['Attribute'])


    def backwards(self, orm):
        # Deleting model 'Style'
        db.delete_table(u'layers_style')

        # Deleting model 'Layer'
        db.delete_table(u'layers_layer')

        # Removing M2M table for field styles on 'Layer'
        db.delete_table(db.shorten_name(u'layers_layer_styles'))

        # Deleting model 'UploadSession'
        db.delete_table(u'layers_uploadsession')

        # Deleting model 'LayerFile'
        db.delete_table(u'layers_layerfile')

        # Deleting model 'Attribute'
        db.delete_table(u'layers_attribute')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'base.contactrole': {
            'Meta': {'unique_together': "(('contact', 'resource', 'role'),)", 'object_name': 'ContactRole'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['people.Profile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.ResourceBase']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'base.license': {
            'Meta': {'ordering': "('name',)", 'object_name': 'License'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'license_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'license_text_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'license_text_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name_es': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'})
        },
        u'base.region': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Region'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'name_es': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['base.Region']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'base.resourcebase': {
            'Meta': {'object_name': 'ResourceBase'},
            'abstract': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bbox_x0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_x1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y0': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'bbox_y1': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '19', 'decimal_places': '10', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.TopicCategory']", 'null': 'True', 'blank': 'True'}),
            'constraints_other': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['people.Profile']", 'through': u"orm['base.ContactRole']", 'symmetrical': 'False'}),
            'csw_anytext': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'csw_insert_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'csw_mdsource': ('django.db.models.fields.CharField', [], {'default': "'local'", 'max_length': '256'}),
            'csw_schema': ('django.db.models.fields.CharField', [], {'default': "'http://www.isotc211.org/2005/gmd'", 'max_length': '64'}),
            'csw_type': ('django.db.models.fields.CharField', [], {'default': "'dataset'", 'max_length': '32'}),
            'csw_typename': ('django.db.models.fields.CharField', [], {'default': "'gmd:MD_Metadata'", 'max_length': '32'}),
            'csw_wkt_geometry': ('django.db.models.fields.TextField', [], {'default': "'POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))'"}),
            'data_quality_statement': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_type': ('django.db.models.fields.CharField', [], {'default': "'publication'", 'max_length': '255'}),
            'detail_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'distribution_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'edition': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'eng'", 'max_length': '3'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.License']", 'null': 'True', 'blank': 'True'}),
            'maintenance_frequency': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'metadata_uploaded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'metadata_xml': ('django.db.models.fields.TextField', [], {'default': '\'<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>\'', 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_resource'", 'null': 'True', 'to': u"orm['people.Profile']"}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_base.resourcebase_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'popular_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'purpose': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rating': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'regions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['base.Region']", 'null': 'True', 'blank': 'True'}),
            'restriction_code_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.RestrictionCodeType']", 'null': 'True', 'blank': 'True'}),
            'share_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'spatial_representation_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.SpatialRepresentationType']", 'null': 'True', 'blank': 'True'}),
            'srid': ('django.db.models.fields.CharField', [], {'default': "'EPSG:4326'", 'max_length': '255'}),
            'supplemental_information': ('django.db.models.fields.TextField', [], {'default': "u'No information provided'"}),
            'temporal_extent_end': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'temporal_extent_start': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        u'base.restrictioncodetype': {
            'Meta': {'ordering': "('identifier',)", 'object_name': 'RestrictionCodeType'},
            'description': ('django.db.models.fields.TextField', [], {'max_length': '255'}),
            'description_en': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description_es': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gn_description': ('django.db.models.fields.TextField', [], {'max_length': '255'}),
            'gn_description_en': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gn_description_es': ('django.db.models.fields.TextField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'is_choice': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'base.spatialrepresentationtype': {
            'Meta': {'ordering': "('identifier',)", 'object_name': 'SpatialRepresentationType'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description_es': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gn_description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gn_description_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gn_description_es': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'is_choice': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'base.topiccategory': {
            'Meta': {'ordering': "('identifier',)", 'object_name': 'TopicCategory'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'gn_description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True'}),
            'gn_description_en': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'gn_description_es': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'location'", 'max_length': '255'}),
            'is_choice': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'layers.attribute': {
            'Meta': {'object_name': 'Attribute'},
            'attribute': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'attribute_label': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'attribute_type': ('django.db.models.fields.CharField', [], {'default': "'xsd:string'", 'max_length': '50'}),
            'average': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'display_order': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_stats_updated': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'layer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attribute_set'", 'to': u"orm['layers.Layer']"}),
            'max': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'median': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'min': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'stddev': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'sum': ('django.db.models.fields.CharField', [], {'default': "'NA'", 'max_length': '255', 'null': 'True'}),
            'unique_values': ('django.db.models.fields.TextField', [], {'default': "'NA'", 'null': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'layers.layer': {
            'Meta': {'object_name': 'Layer', '_ormbases': [u'base.ResourceBase']},
            'abstract_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'abstract_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'charset': ('django.db.models.fields.CharField', [], {'default': "'UTF-8'", 'max_length': '255'}),
            'constraints_other_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'constraints_other_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'data_quality_statement_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'data_quality_statement_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'default_style': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'layer_default_style'", 'null': 'True', 'to': u"orm['layers.Style']"}),
            'distribution_description_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_description_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'purpose_en': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'purpose_es': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'resourcebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['base.ResourceBase']", 'unique': 'True', 'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'layer_set'", 'null': 'True', 'to': u"orm['services.Service']"}),
            'store': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'storeType': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'styles': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'layer_styles'", 'symmetrical': 'False', 'to': u"orm['layers.Style']"}),
            'supplemental_information_en': ('django.db.models.fields.TextField', [], {'default': "u'No information provided'", 'null': 'True', 'blank': 'True'}),
            'supplemental_information_es': ('django.db.models.fields.TextField', [], {'default': "u'No information provided'", 'null': 'True', 'blank': 'True'}),
            'title_en': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title_es': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'typename': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'upload_session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['layers.UploadSession']", 'null': 'True', 'blank': 'True'}),
            'workspace': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        u'layers.layerfile': {
            'Meta': {'object_name': 'LayerFile'},
            'base': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'upload_session': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['layers.UploadSession']"})
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
        },
        u'layers.uploadsession': {
            'Meta': {'object_name': 'UploadSession'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'traceback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['people.Profile']"})
        },
        u'people.profile': {
            'Meta': {'object_name': 'Profile'},
            'area': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'delivery': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'organization': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'profile': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'voice': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'services.service': {
            'Meta': {'object_name': 'Service', '_ormbases': [u'base.ResourceBase']},
            'access_constraints': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'api_key': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'base_url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'connection_params': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'external_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fees': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'first_noanswer': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'noanswer_retries': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'online_resource': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'service_set'", 'null': 'True', 'to': u"orm['services.Service']"}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'profiles': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['people.Profile']", 'through': u"orm['services.ServiceProfileRole']", 'symmetrical': 'False'}),
            u'resourcebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['base.ResourceBase']", 'unique': 'True', 'primary_key': 'True'}),
            'resources_ref': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'store_ref': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'workspace_ref': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'services.serviceprofilerole': {
            'Meta': {'object_name': 'ServiceProfileRole'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profiles': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['people.Profile']"}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['services.Service']"})
        }
    }

    complete_apps = ['layers']