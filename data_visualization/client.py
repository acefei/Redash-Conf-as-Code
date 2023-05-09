import httpx


class AsyncAPIClient:
    def __init__(self, redash_url, api_key):
        self.redash_url = redash_url
        self.session = httpx.AsyncClient()
        self.session.headers.update({"Authorization": "Key {}".format(api_key)})

    async def _get(self, path, **kwargs):
        return await self._request("GET", path, **kwargs)

    async def _post(self, path, **kwargs):
        return await self._request("POST", path, **kwargs)

    async def _delete(self, path, **kwargs):
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method, path, **kwargs):
        url = "{}/{}".format(self.redash_url, path)
        response = await self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    async def get_data_source_id(self, data_source_name=None)->str:
        res = await self._get("api/data_sources")
        for ds in res.json():
            if data_source_name:
                if ds['name'] == data_source_name:
                    return ds['id']
            # return the first data_source by default if data_source_name is None.
            else:
                return ds['id']
        return ''

    async def update_query(self, query_id, data) -> str:
        res = await self._post(f"api/queries/{query_id}", json=data)
        return res.json()

    async def update_dashboard(self, dash_id, data) -> str:
        res = await self._post(f"api/dashboards/{dash_id}", json=data)
        return res.json()['id']

    async def update_visualization(self, viz_id, data ):
        res = await self._post(f"api/visualizations/{viz_id}", json=data)
        return res.json()['id']

    async def list_queries(self) -> list:
        res = await self._get("api/queries")
        return res.json()['results']

    async def list_dashboards(self):
        res = await self._get("api/dashboards")
        return res.json()['results']

    async def get_query(self, id):
        res = await self._get(f"api/queries/{id}")
        return res.json()

    async def get_dashboard(self, id):
        res = await self._get(f"api/dashboards/{id}")
        return res.json()

    async def create_dashboard(self, name) -> str:
        res = await self._post("api/dashboards", json={'name': name})
        return res.json()['id']

    async def create_query(self, query_json) -> str:
        res = await self._post("api/queries", json=query_json)
        return res.json()['id']

    async def create_widget(self, widget_json):
        res = await self._post("api/widgets", json=widget_json)
        return res.json()['id']

    async def create_visualization(self, viz_json):
        res = await self._post("api/visualizations", json=viz_json)
        return res.json()['id']

    async def delete_queries(self):
        queries = await self.list_queries()
        for q in queries:
            await self._delete(f"api/queries/{q['id']}")

    async def delete_dashboards(self):
        dashboards = await self.list_dashboards()
        for d in dashboards:
            await self._delete(f"api/dashboards/{d['id']}")

    async def clean(self):
        await self.delete_dashboards()
        await self.delete_queries()
