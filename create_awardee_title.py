import datetime
from core.models import Title, Language, Country, Awardee

Awardee.objects.get_or_create(org_code="lamasca", name="La Masca")
Title.objects.all().delete()
title = Title.objects.create(
    lccn = "sn00000001",    # This needs to be unique across the platform
    lccn_orig = "sn00000001",
    name = "La masca",
    name_normal = "la-masca",
    start_year = "1994",
    end_year = "1994",
    country = Country.objects.get(code="it"),
    version = datetime.datetime.now()
)
title.languages.set([Language.objects.get(code="ita")])
