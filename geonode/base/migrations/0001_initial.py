# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ContactRole'
        db.create_table(u'base_contactrole', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.ResourceBase'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['people.Profile'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'base', ['ContactRole'])

        # Adding unique constraint on 'ContactRole', fields ['contact', 'resource', 'role']
        db.create_unique(u'base_contactrole', ['contact_id', 'resource_id', 'role'])

        # Adding model 'TopicCategory'
        db.create_table(u'base_topiccategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(default='location', max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('description_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('gn_description', self.gf('django.db.models.fields.TextField')(default='', null=True)),
            ('gn_description_en', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('gn_description_es', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('is_choice', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'base', ['TopicCategory'])

        # Adding model 'SpatialRepresentationType'
        db.create_table(u'base_spatialrepresentationtype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description_en', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('description_es', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('gn_description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('gn_description_en', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('gn_description_es', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('is_choice', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'base', ['SpatialRepresentationType'])

        # Adding model 'Region'
        db.create_table(u'base_region', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name_en', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('name_es', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('parent', self.gf('mptt.fields.TreeForeignKey')(blank=True, related_name='children', null=True, to=orm['base.Region'])),
            (u'lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            (u'level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'base', ['Region'])

        # Adding model 'RestrictionCodeType'
        db.create_table(u'base_restrictioncodetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=255)),
            ('description_en', self.gf('django.db.models.fields.TextField')(max_length=255, null=True, blank=True)),
            ('description_es', self.gf('django.db.models.fields.TextField')(max_length=255, null=True, blank=True)),
            ('gn_description', self.gf('django.db.models.fields.TextField')(max_length=255)),
            ('gn_description_en', self.gf('django.db.models.fields.TextField')(max_length=255, null=True, blank=True)),
            ('gn_description_es', self.gf('django.db.models.fields.TextField')(max_length=255, null=True, blank=True)),
            ('is_choice', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'base', ['RestrictionCodeType'])

        # Adding model 'Thumbnail'
        db.create_table(u'base_thumbnail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resourcebase', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.ResourceBase'])),
            ('thumb_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('thumb_spec', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('version', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, null=True)),
        ))
        db.send_create_signal(u'base', ['Thumbnail'])

        # Adding model 'License'
        db.create_table(u'base_license', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name_en', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('name_es', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=2000, null=True, blank=True)),
            ('license_text', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('license_text_en', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('license_text_es', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'base', ['License'])

        # Adding model 'ResourceBase'
        db.create_table(u'base_resourcebase', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('polymorphic_ctype', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'polymorphic_base.resourcebase_set', null=True, to=orm['contenttypes.ContentType'])),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owned_resource', null=True, to=orm['people.Profile'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('date_type', self.gf('django.db.models.fields.CharField')(default='publication', max_length=255)),
            ('edition', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('abstract', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('purpose', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('maintenance_frequency', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('restriction_code_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.RestrictionCodeType'], null=True, blank=True)),
            ('constraints_other', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('license', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.License'], null=True, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='eng', max_length=3)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.TopicCategory'], null=True, blank=True)),
            ('spatial_representation_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.SpatialRepresentationType'], null=True, blank=True)),
            ('temporal_extent_start', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('temporal_extent_end', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('supplemental_information', self.gf('django.db.models.fields.TextField')(default=u'No information provided')),
            ('distribution_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('distribution_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('data_quality_statement', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bbox_x0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('bbox_x1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('bbox_y0', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('bbox_y1', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=19, decimal_places=10, blank=True)),
            ('srid', self.gf('django.db.models.fields.CharField')(default='EPSG:4326', max_length=255)),
            ('csw_typename', self.gf('django.db.models.fields.CharField')(default='gmd:MD_Metadata', max_length=32)),
            ('csw_schema', self.gf('django.db.models.fields.CharField')(default='http://www.isotc211.org/2005/gmd', max_length=64)),
            ('csw_mdsource', self.gf('django.db.models.fields.CharField')(default='local', max_length=256)),
            ('csw_insert_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('csw_type', self.gf('django.db.models.fields.CharField')(default='dataset', max_length=32)),
            ('csw_anytext', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('csw_wkt_geometry', self.gf('django.db.models.fields.TextField')(default='POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))')),
            ('metadata_uploaded', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('metadata_xml', self.gf('django.db.models.fields.TextField')(default='<gmd:MD_Metadata xmlns:gmd="http://www.isotc211.org/2005/gmd"/>', null=True, blank=True)),
            ('popular_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('share_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('featured', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('thumbnail_url', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('detail_url', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('rating', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
        ))
        db.send_create_signal(u'base', ['ResourceBase'])

        # Adding M2M table for field regions on 'ResourceBase'
        m2m_table_name = db.shorten_name(u'base_resourcebase_regions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('resourcebase', models.ForeignKey(orm[u'base.resourcebase'], null=False)),
            ('region', models.ForeignKey(orm[u'base.region'], null=False))
        ))
        db.create_unique(m2m_table_name, ['resourcebase_id', 'region_id'])

        # Adding model 'Link'
        db.create_table(u'base_link', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['base.ResourceBase'])),
            ('extension', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('link_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('mime', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('url', self.gf('django.db.models.fields.TextField')(max_length=1000)),
        ))
        db.send_create_signal(u'base', ['Link'])


    def backwards(self, orm):
        # Removing unique constraint on 'ContactRole', fields ['contact', 'resource', 'role']
        db.delete_unique(u'base_contactrole', ['contact_id', 'resource_id', 'role'])

        # Deleting model 'ContactRole'
        db.delete_table(u'base_contactrole')

        # Deleting model 'TopicCategory'
        db.delete_table(u'base_topiccategory')

        # Deleting model 'SpatialRepresentationType'
        db.delete_table(u'base_spatialrepresentationtype')

        # Deleting model 'Region'
        db.delete_table(u'base_region')

        # Deleting model 'RestrictionCodeType'
        db.delete_table(u'base_restrictioncodetype')

        # Deleting model 'Thumbnail'
        db.delete_table(u'base_thumbnail')

        # Deleting model 'License'
        db.delete_table(u'base_license')

        # Deleting model 'ResourceBase'
        db.delete_table(u'base_resourcebase')

        # Removing M2M table for field regions on 'ResourceBase'
        db.delete_table(db.shorten_name(u'base_resourcebase_regions'))

        # Deleting model 'Link'
        db.delete_table(u'base_link')


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
        u'base.link': {
            'Meta': {'object_name': 'Link'},
            'extension': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mime': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.ResourceBase']"}),
            'url': ('django.db.models.fields.TextField', [], {'max_length': '1000'})
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
        u'base.thumbnail': {
            'Meta': {'object_name': 'Thumbnail'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resourcebase': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['base.ResourceBase']"}),
            'thumb_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'thumb_spec': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'version': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True'})
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
        }
    }

    complete_apps = ['base']