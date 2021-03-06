# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from .views import DocumentUploadView, DocumentUpdateView, DocumentAppendView

js_info_dict = {
    'packages': ('geonode.tabular',),
}

urlpatterns = patterns('geonode.tabular.views',
                       url(r'^$',
                           login_required(TemplateView.as_view(template_name='tabular/document_list.html')),
                           name='tabular_browse'),
                       url(r'^(?P<docid>\d+)/?$',
                           'document_detail',
                           name='tabular_detail'),
                       url(r'^(?P<docid>\d+)/download/?$',
                           'document_download',
                           name='tabular_download'),
                       url(r'^(?P<docid>\d+)/replace$',
                           login_required(DocumentUpdateView.as_view()),
                           name="tabular_replace"),
                       url(r'^(?P<docid>\d+)/append$',
                           login_required(DocumentAppendView.as_view()),
                           name="tabular_append"),                       
                       url(r'^(?P<docid>\d+)/remove$',
                           'document_remove',
                           name="tabular_remove"),
                       url(r'^upload/?$',
                           login_required(DocumentUploadView.as_view()),
                           name='tabular_upload'),
                       url(r'^search/?$',
                           'document_search_page',
                           name='tabular_search_page'),
                       url(r'^(?P<docid>\d+)/metadata$',
                           'document_metadata',
                           name='tabular_metadata'),
                       )
