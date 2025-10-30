import os
from pathlib import Path
from django.conf import settings


app_name = 'project_python'
app_dir = Path(__file__).resolve().parent
app_cache_dir = app_dir / 'cache'
app_data_dir = app_dir / 'data'

pycharm_download_json = app_data_dir / 'pycharm.json'

user_data_dir = settings.DATA_ROOT / app_name
user_config_file = user_data_dir / 'config.json'
user_project_file = user_data_dir / 'project.json'
user_pycharm_file = user_data_dir / 'pycharm.json'

pycharm_settings_dir_prefix = os.path.join(os.environ.get('APPDATA'), 'JetBrains')
pycharm_cache_dir_prefix =  os.path.join(os.environ.get('LOCALAPPDATA'), 'JetBrains')

emplty_sdk_xml_content = """<application>
  <component name="ProjectJdkTable">
  </component>
</application>
"""

sdk_new_str = """   <jdk version="2">
      <name value="{sdk_name}" />
      <type value="Python SDK" />
      <version value="{sdk_version}" />
      <homePath value="{sdk_path}python.exe" />
      <roots>
        <classPath>
          <root type="composite">
            <root url="file://{sdk_path}DLLs" type="simple" />
            <root url="file://{sdk_path}Lib" type="simple" />
            <root url="file://{sdk_path}" type="simple" />
            <root url="file://{sdk_path}Lib/site-packages" type="simple" />
            <root url="file://$APPLICATION_HOME_DIR$/plugins/python-ce/helpers/typeshed/stdlib" type="simple" />
          </root>
        </classPath>
        <sourcePath>
          <root type="composite" />
        </sourcePath>
      </roots>
      <additional SDK_UUID="{sdk_uuid}">
        <setting name="FLAVOR_ID" value="WinPythonSdkFlavor" />
        <setting name="FLAVOR_DATA" value="{}" />
      </additional>
    </jdk>
"""
project_xml_str = """        <entry key="{{project_dir}}">
          <value>
          <RecentProjectMetaInfo frameTitle="{{project_name}}" opened="false">
          </RecentProjectMetaInfo>
          </value>
        </entry>
"""

project_misc_content = """<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="ProjectRootManager" version="2" project-jdk-name="" project-jdk-type="Python SDK" />
</project>
"""