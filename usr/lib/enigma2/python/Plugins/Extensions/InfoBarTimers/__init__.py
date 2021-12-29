from gettext import bindtextdomain, dgettext, gettext

from Components.Language import language
from Tools.Directories import SCOPE_PLUGINS, resolveFilename

PluginLanguageDomain = "InfoBarTimers"
PluginLanguagePath = "Extensions/InfoBarTimers/locale"


def localeInit():
	bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	_txt = dgettext(PluginLanguageDomain, txt)
	if _txt:
		return _txt
	else:
		print("[%s] Fall back to default translation for '%s'." % (PluginLanguageDomain, txt))
		return gettext(txt)


localeInit()
language.addCallback(localeInit)
