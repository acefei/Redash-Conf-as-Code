import argparse
import asyncio
import pathlib

import aiofiles
import yaml
from client import AsyncAPIClient

QUERY_PATH=pathlib.Path('data_visualization/queries')
DASHBOARD_PATH=pathlib.Path('data_visualization/dashboards')

class literal(str):
    pass

def literal_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
yaml.add_representer(literal, literal_presenter)

class Migration:
    def __init__(self, redash_url, api_key):
        self.rc = AsyncAPIClient(redash_url, api_key)
        self.cwd = pathlib.Path(__file__).resolve().parent
        # To create dashboard needs visualization id, but there is no redash api to get visualizations,
        # See https://github.com/getredash/redash/blob/v10.1.0/redash/handlers/visualizations.py
        # So here need a mapping for old and new visualization id.
        self.viz_id_mapping = {}

    async def export_queries(self):
        QUERY_PATH.mkdir(parents=True,exist_ok=True)

        queries = await self.rc.list_queries()
        for q in queries:
            query = await self.rc.get_query(q['id'])
            data = {
                "data_source_id": query['data_source_id'],
                "query": literal(query["query"]),
                "description": query["description"],
                "name": query["name"],
                "options": query["options"],
                "tags": query["tags"],
                "is_draft": query["is_draft"],
                "visualizations": query["visualizations"]
            }

            async with aiofiles.open(QUERY_PATH / f"{query['name']}.yaml", "w") as fout:
                await fout.write(yaml.dump(data))

    async def import_queries(self):
        for jp in QUERY_PATH.glob('*.yaml'):
            async with aiofiles.open(jp) as fin:
                raw = await fin.read()
                data = yaml.safe_load(raw)

            # set data source id
            if not data.get('data_source_id'):
                data['data_source_id'] = await self.rc.get_data_source_id()

            query_required = data.copy()
            visualizations = query_required.pop('visualizations')
            query_id = await self.rc.create_query(query_required)

            for viz in visualizations:
                match viz["type"]:
                    # There is a default table created with query,
                    # Only update table visualization here
                    case "TABLE":
                        res = await self.rc.get_query(query_id)
                        new_table_viz_id = res['visualizations'][0]['id']

                        data = {
                                "name": viz["name"],
                                "description": viz["description"],
                                "options": viz["options"]
                        }
                        await self.rc.update_visualization(new_table_viz_id, data)
                    case _:
                        data = {
                            "name": viz["name"],
                            "description": viz["description"],
                            "options": viz["options"],
                            "type": viz["type"],
                            "query_id":query_id,
                        }
                        new_viz_id = await self.rc.create_visualization(data)
                        self.viz_id_mapping[viz['id']] = new_viz_id

            # publish as original status.
            if not data.get("is_draft"):
                await self.rc.update_query(query_id, {"is_draft": False})


    async def export_dashboards(self):
        DASHBOARD_PATH.mkdir(parents=True,exist_ok=True)
        dashboards = await self.rc.list_dashboards()
        for dashboard in dashboards:
            dashboard = await self.rc.get_dashboard(dashboard['id'])

            data = {
                "name": dashboard['name'],
                "is_draft": dashboard['is_draft'],
            }
            for widget in dashboard['widgets']:
                # Don't need all visualization info, only ID is required to create the dashboard.
                viz = widget.pop('visualization')
                widget['visualization_id'] = viz["id"]

            data['widgets'] = dashboard['widgets']
            async with aiofiles.open(DASHBOARD_PATH / f"{dashboard['name']}.yaml", "w") as fout:
                await fout.write(yaml.dump(data))

    async def import_dashboards(self):
        for jp in DASHBOARD_PATH.glob('*.yaml'):
            async with aiofiles.open(jp) as fin:
                raw = await fin.read()
                data = yaml.safe_load(raw)

            dash_id = await self.rc.create_dashboard(data['name'])
            for widget in data['widgets']:
                widget_required = {
                    "dashboard_id": dash_id,
                    "width": widget["width"],
                    "text": widget["text"],
                    "options": widget["options"],
                    "visualization_id": self.viz_id_mapping.get(widget["visualization_id"])
                }
                await self.rc.create_widget(widget_required)

                # publish as original status.
                if not data.get("is_draft"):
                    await self.rc.update_dashboard(dash_id, {"is_draft": False})



def get_args():
    parser = argparse.ArgumentParser(description='Perform backup or recovery operation for a URL with a specified API key.')
    parser.add_argument('url', type=str)
    parser.add_argument('apikey', type=str)
    parser.add_argument('action', type=str, choices=['backup', 'recovery', 'clean'], help='operation to perform')

    return parser.parse_args()


async def main():
    args = get_args()
    m = Migration(args.url, args.apikey)
    match args.action:
        case "backup":
            await m.export_dashboards()
            await m.export_queries()
        case "recovery":
            # import queries first as it will create visualization for dashboard
            await m.import_queries()
            await m.import_dashboards()
        case "clean":
            await m.rc.clean()

asyncio.run(main())
