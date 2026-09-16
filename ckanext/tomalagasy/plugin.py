import os

import ckan.plugins as p
import ckan.plugins.toolkit as tk

I18N_DIR = os.path.join(os.path.dirname(__file__), "i18n")
LOCALES = ["mg", "fr", "en"]


class ToMalagasyPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)

    def update_config(self, config):
        if not os.path.isfile(os.path.join(I18N_DIR, "mg", "LC_MESSAGES", "ckan.mo")):
            raise RuntimeError(
                "ckanext-tomalagasy: no compiled catalog in %s — run "
                "`python -m ckanext.tomalagasy.catalog build`" % I18N_DIR
            )

        # CKAN only offers locales that exist as directories in
        # ckan.i18n_directory, and loads its core `ckan` domain from there. The
        # built folder holds exactly mg (with French filling the gaps) and fr,
        # so pointing CKAN at it is what makes `mg` a valid default.
        config["ckan.i18n_directory"] = I18N_DIR
        config["ckan.locale_default"] = LOCALES[0]
        config["ckan.locales_offered"] = LOCALES
        config["ckan.locale_order"] = LOCALES

        tk.add_template_directory(config, "templates")
        tk.add_resource("assets", "tomalagasy")
