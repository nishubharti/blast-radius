# standard libraries
from glob import iglob
import io
import os
import re

# 3rd party libraries
import hcl2 as hcl   # hashicorp configuration language (.tf)

class Terraform:
    """Finds terraform/hcl files (*.tf) in CWD or a supplied directory, parses
    them with pyhcl, and exposes the configuration via self.config."""

    def __init__(self, directory=None, settings=None):
        self.settings = settings if settings else {}

        # handle the root module first...
        self.directory = directory if directory else os.getcwd()
        #print(self.directory)
        self.config_str = ''
        iterator = iglob( self.directory + '/*.tf')
        for fname in iterator:
            with open(fname, 'r', encoding='utf-8') as f:
                self.config_str += f.read() + ' '
        
        config_io = io.StringIO(self.config_str)
        self.config = hcl.load(config_io)

        # then any submodules it may contain, skipping any remote modules for
        # the time being.
        self.modules = {}
        if 'module' in self.config:
            for name, mod in self.config['module'].items():
                if 'source' not in mod:
                    continue
                source = mod['source']
                # '//' used to refer to a subdirectory in a git repo
                if re.match(r'.*\/\/.*', source):
                    continue
                # '@' should only appear in ssh urls
                elif re.match(r'.*\@.*', source):
                    continue
                # 'github.com' special behavior.
                elif re.match(r'github\.com.*', source):
                    continue
                # points to new TFE module registry
                elif re.match(r'app\.terraform\.io', source):
                    continue
                # bitbucket public and private repos
                elif re.match(r'bitbucket\.org.*', source):
                    continue
                # git::https or git::ssh sources
                elif re.match(r'^git::', source):
                    continue
                # git:// sources
                elif re.match(r'^git:\/\/', source):
                    continue
                # Generic Mercurial repos
                elif re.match(r'^hg::', source):
                    continue
                # Public Terraform Module Registry
                elif re.match(r'^[a-zA-Z0-9\-_]+\/[a-zA-Z0-9\-_]+\/[a-zA-Z0-9\-_]+', source):
                    continue
                # AWS S3 buckets
                elif re.match(r's3.*\.amazonaws\.com', source):
                    continue
                # fixme path join. eek.
                self.modules[name] = Terraform(directory=self.directory+'/'+source, settings=mod)


    def get_def(self, node, module_depth=0):

        # FIXME 'data' resources (incorrectly) handled as modules, necessitating
        # the try/except block here.
        if len(node.modules) > module_depth and node.modules[0] != 'root':
            try:
                tf = self.modules[ node.modules[module_depth] ]
                return tf.get_def(node, module_depth=module_depth+1)
            except:
                return ''

        try:
            # non resource types
            # types = { 'var'  : lambda x: self.config['variable'][x.resource_name],
            # 'provider'     : lambda x: self.config['provider'][x.resource_name],
            # 'output'       : lambda x: self.config['output'][x.resource_name],
            # 'data'         : lambda x: self.config['data'][x.resource_name],
            # 'meta'         : lambda x: '',
            # 'provisioner'  : lambda x: '',
            # ''             : lambda x: '' }
            # types = {'output','data','provider'}

#for simple graphs we do not need these information in json 

            # if node.type in types:
            #     for n in self.config[node.type]:
            #         if node.resource_name in n:
            #             return n[node.resource_name]

            #     return ''
            
            # if node.type == 'var':
            #     for n in self.config['variable']:
            #         if node.resource_name in n:
            #             return n[node.resource_name]

            #     return ''

            # resources are a little different _many_ possible types,
            # nested within the 'resource' field.
            # else:
                
            for n in self.config['resource']:
                if node.type in n:
                    if node.resource_name in n[node.type]:
                        return n[node.type][node.resource_name]
                
            return ''

                # return self.config['resource'][0][node.type][node.resource_name]
        except:
            return ''