# -*- coding: utf-8 -*-
#
# This work by Hazard-SJ ( https://github.com/HazardSJ ) is licensed under a
# Creative Commons Attribution-ShareAlike 4.0 International License ( http://creativecommons.org/licenses/by-sa/4.0/ ).


from datetime import datetime
import re
import mwparserfromhell
import pywikibot


pywikibot.config.family = "wikidata"
pywikibot.config.mylang = "wikidata"

site = pywikibot.Site()
site.login()


class RFORArchiverBot(object):
    """Archives closed requests on [[Wikidata:Requests for permissions/Other rights]]"""

    def __init__(self):
        self.base_page = pywikibot.Page(site, "Wikidata:Requests for permissions")
        self.requests_page = pywikibot.Page(site, self.base_page.title() + "/Other rights")
        self.archive_titles = {
            "confirmed": self.base_page.title() + "/RfConfirmed/%s",
            # "ipblock-exempt": self.basePage.title() + "",  # Not archived currently
            "propertycreator": self.base_page.title() + "/RfPropertyCreator/%s",
            "rollbacker": self.base_page.title() + "/RfRollback/%s"
        }
        self.closed_regex = "\n\{\{\s*(?:A(?:rchive)?|D(?:iscussion)?) ?top\|.*?\}\}.*?"
        self.closed_regex += "\{\{\s*(?:A(?:rchive)?|D(?:iscussion)?) ?bottom\}\}\n"
        self.archive_text = "{{Archive|category=Archived requests for permissions}}"
        self.archive_text += "\n__TOC__\n{{Discussion top}}"

    def run(self):
        text = self.requests_page.get()
        code = mwparserfromhell.parser.Parser().parse(text, skip_style_tags=True)
        for section in code.get_sections(levels=[2]):
            if "confirmed" in section.filter_headings()[0].title.lower():
                group = "confirmed"
            elif "property" in section.filter_headings()[0].title.lower():
                group = "propertycreator"
            elif "rollback" in section.filter_headings()[0].title.lower():
                group = "rollbacker"
            else:
                continue
            archivable = list()
            for discussion in section.get_sections(levels=[4]):
                templates = [template.name.lower().strip() for template in discussion.ifilter_templates()]
                if not ("done" in templates or "not done" in templates or "notdone" in templates):
                    continue
                timestamps = re.findall(
                    "\d{1,2}:\d{2},\s\d{1,2}\s\D{3,9}\s\d{4}\s\(UTC\)", discussion.__unicode__()
                )
                timestamps = sorted(
                    [datetime.strptime(timestamp[:-6], "%H:%M, %d %B %Y") for timestamp in timestamps]
                )
                if (datetime.utcnow() - timestamps[-1]).days >= 5:
                    archivable.append(discussion)
            if not archivable:
                continue
            archive = pywikibot.Page(
                site,
                self.archive_titles[group] % datetime.utcnow().strftime("%B %Y")
            )
            if archive.exists():
                archive_text = archive.get()
            else:
                archive_text = self.archive_text
                archive_text += "\n\n"
            archive_code = mwparserfromhell.parse(archive_text)
            for add in archivable:
                append = add.strip()
                if append not in archive_code:
                    archive_code.append(append + "\n\n")
            for remove in archivable:
                code.remove(remove)
            archive.put(
                archive_code,
                "[[Wikidata:Bots|Bot]]: Archiving from %s" % self.requests_page.title(asLink=True)
            )
        pywikibot.showDiff(text, code)
        if text != code:
            self.requests_page.put(code, "[[Wikidata:Bots|Bot]]: Archived closed requests")


def main():
    bot = RFORArchiverBot()
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
