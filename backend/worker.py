import os
from django.core.wsgi import get_wsgi_application
from workers import WorkerEntrypoint, wsgi

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = request.url
        if "/api/" in url or url.endswith("/api") or "/admin/" in url:
            return await wsgi.fetch(application, request, self.env)
        return await self.env.ASSETS.fetch(request)

    async def scheduled(self, controller, env, ctx):
        # Process due jobs once per invocation; never run an infinite loop in Workers.
        from health.cloudflare_jobs import process_due_jobs
        process_due_jobs()
