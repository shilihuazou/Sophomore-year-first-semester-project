from django.contrib import admin
from .models import MapMarker, MarkerReport, Mission, MissionReport, Team

admin.site.register(Team)
admin.site.register(Mission)
admin.site.register(MissionReport)
admin.site.register(MapMarker)
admin.site.register(MarkerReport)
