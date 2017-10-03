#!/usr/bin/env python

import subprocess
import json

class CloudFoundry:

    def __init__(self):
        self._entity_cache = {}

    def curl(self, url):
        """Calls given url, parses json, returns json doc."""
        # this is actually a terrible way to do this, as cf curl doesn't
        # have any way to fail on non-200
        api_output = subprocess.check_output(['cf', 'curl', url]) 
        doc = json.loads(api_output) 
        if doc == None:
            sys.stderr.write(api_output) 
            raise ValueError

        return doc

    def api_call(self, url):
        """make all the API calls needed, and return a doc"""
        api_result = doc = self.curl(url)
        while doc['total_pages'] > 1 and doc['next_url'] is not None:
            doc = self.curl(doc['next_url'])
            api_result['resources'] += doc['resources']
        return api_result

    def resolve_entity_attr(self, url, attr="name"):
        """Given a cf url, resolve the name of the entity

        e.g. name = resolve_entity_attr('/v2/service_plans/1811bcda-ef6c-4ae0-adda-a5807ef198c9')"""
        if self._entity_cache.has_key(url):
            doc = self._entity_cache[url] 
        else:
            doc = self.curl(url)
            self._entity_cache[url] = doc

        return doc['entity'][attr]

    def plan(self, url):
        doc = self.curl(url)
        planname = doc['entity']['name']
        servicename = self.resolve_entity_attr(doc['entity']['service_url'], 'label')
        return (planname, servicename)

    def space(self, url):
        """Given a URL returns (spacename, orgname)"""
        doc = self.curl(url)
        try:
            spacename = doc['entity']['name']
        except KeyError:
            if doc.has_key('error_code'):
                spacename = doc['error_code']
            else: 
                raise ValueError
        try:
            orgname = self.resolve_entity_attr(doc['entity']['organization_url'])
        except KeyError:
            orgname = 'CF-OrganizationNotFound'
        return (spacename, orgname)

    def service_instances(self):
        """Returns a list of dicts of service instances for current CF org"""
        service_instances = self.curl('/v2/service_instances')
        
        output = []
        for resource in service_instances['resources']:
            service_instance = resource['entity'] 
            s = {}
            s['name'] = service_instance['name']
            (s['plan'],s['service']) = self.plan(service_instance['service_plan_url'])
            (s['space'], s['org']) = self.space(service_instance['space_url'])
            
            output.append(s)
        
        return output       

    def apps(self):
        """Returns a list of dicts of service instances for current CF org"""
        apps = self.api_call('/v2/apps')

        fields = ['name', 'org', 'space', 'buildpack', 'detected_buildpack']
        
        output = [fields]
        for resource in apps['resources']:
            app = resource['entity'] 
            (app['space'], app['org']) = self.space(app['space_url'])
            s = [app[k] for k in fields]
            
            output.append(s)
        
        return output       

