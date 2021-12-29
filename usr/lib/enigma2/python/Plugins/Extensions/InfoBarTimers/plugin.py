##############################################################################
#
# 	InfoBarTimers Plugin for Enigma-2
# 	Coded by IanSav (c) 2018-2019  <IS.OzPVR(at)gmail.com>
#	Assistance, improvements and optimisations provided by Prl.
#
# 	Based on ideas from InfoBarTunerState Plugin
# 	Coded by betonme (c) 2011  <glaserfrank(at)gmail.com>
#
# 	This program is free software; you can redistribute it and/or modify
# 	it under the terms of the GNU General Public License as published by
# 	the Free Software Foundation; either version 2 of the License, or
# 	(at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful, but
# 	WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# 	General Public License for more details.
#
##############################################################################

from operator import attrgetter

from enigma import ePoint, eSize, eTimer, getDesktop
from time import localtime, strftime, time

from Components.ActionMap import HelpableActionMap
from Components.config import ConfigEnableDisable, ConfigInteger, ConfigSelection, ConfigSelectionNumber, ConfigSequence, ConfigSubsection, ConfigYesNo, config
from Components.Pixmap import MultiPixmap
from Components.PluginComponent import plugins
from Components.Renderer.Picon import getPiconName
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.HelpMenu import HelpableScreen
from Screens.InfoBarGenerics import InfoBarShowHide, isMoviePlayerInfoBar, isStandardInfoBar
from Screens.Screen import Screen
from Screens.Setup import Setup
from Tools.Directories import SCOPE_CURRENT_PLUGIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap

NAME = _("InfoBarTimers")
SHOW = _("Show Timers")
SETUP = _("InfoBarTimers Setup")
DESCRIPTION = _("InfoBar display of recent, current and pending timers")
VERSION = "0.3.1"

InfoBarShowHide__init__ = None

# Icon images are derived from a skin based MultiPixmap rather than hard coding them.
#
ICON_OFF = 0
ICON_WAIT = 1
ICON_PREP = 2
ICON_REC = 3
ICON_ZAP = 4
ICON_FAIL = 5
ICON_END = 6
ICON_AUTO = 7
ICON_REP = 8

desktopWidth = getDesktop(0).size().width()
desktopHeight = getDesktop(0).size().height()

DEF_ITEMHEIGHT = 25
DEF_ENTRIES = 10
MIN_ENTRIES = 1

orderChoices = [
	("adew", _("Active / Disabled / Ended / Waiting")),
	("adwe", _("Active / Disabled / Waiting / Ended")),
	("aedw", _("Active / Ended / Disabled / Waiting")),
	("aewd", _("Active / Ended / Waiting / Disabled")),
	("awde", _("Active / Waiting / Disabled / Ended")),
	("awed", _("Active / Waiting / Ended / Disabled")),
	("daew", _("Disabled / Active / Ended / Waiting")),
	("dawe", _("Disabled / Active / Waiting / Ended")),
	("deaw", _("Disabled / Ended / Active / Waiting")),
	("dewa", _("Disabled / Ended / Waiting / Active")),
	("dwae", _("Disabled / Waiting / Active / Ended")),
	("dwea", _("Disabled / Waiting / Ended / Active")),
	("eadw", _("Ended / Active / Disabled / Waiting")),
	("eawd", _("Ended / Active / Waiting / Disabled")),
	("edaw", _("Ended / Disabled / Active / Waiting")),
	("edwa", _("Ended / Disabled / Waiting / Active")),
	("ewad", _("Ended / Waiting / Active / Disabled")),
	("ewda", _("Ended / Waiting / Disabled / Active")),
	("waed", _("Waiting / Active / Ended / Disabled")),
	("wade", _("Waiting / Active / Disabled / Ended")),
	("wdae", _("Waiting / Disabled / Active / Ended")),
	("wdea", _("Waiting / Disabled / Ended / Active")),
	("wead", _("Waiting / Ended / Active / Disabled")),
	("weda", _("Waiting / Ended / Disabled / Active"))
]

sortChoices = [
	("0", _("Ascending")),
	("1", _("Descending"))
]

formatChoices = [
	("0", _("Mins/Secs display")),
	("1", _("H:MM:SS display")),
	("2", _("M:SS display")),
	("3", _("H:MM display"))
]

signalChoices = [
	("0", _("None")),
	("1", _("Short (S/Q)")),
	("2", _("Short (P/Q)")),
	("3", _("Long (AGC/SNR)"))
]

separatorChoices = [
	("0", _("None")),
	("1", _("Space")),
	("2", _("Colon ':'")),
	("3", _("Equals '='")),
	("4", _("Hyphen '-'")),
	("5", _("Colon with space ': '")),
	("6", _("Equals with spaces ' = '")),
	("7", _("Hyphen with spaces ' - '"))
]

overlayPositions = {
	720: [50, 140],
	1080: [75, 210]
}

styleChoices = [
	("default", "Default")
]

config.plugins.InfoBarTimers = ConfigSubsection()
config.plugins.InfoBarTimers.enabled = ConfigEnableDisable(default=True)
config.plugins.InfoBarTimers.moviePlayer = ConfigEnableDisable(default=False)
config.plugins.InfoBarTimers.extensionsShow = ConfigYesNo(default=False)
config.plugins.InfoBarTimers.extensionsSetup = ConfigYesNo(default=False)
default = "wade" if config.usage.timerlist_finished_timer_position.value == "end" else "edaw"
config.plugins.InfoBarTimers.orderOverlay = ConfigSelection(default=default, choices=orderChoices)
config.plugins.InfoBarTimers.orderShow = ConfigSelection(default=default, choices=orderChoices)
config.plugins.InfoBarTimers.sortOverlay = ConfigSelection(default="0", choices=sortChoices)
config.plugins.InfoBarTimers.sortShow = ConfigSelection(default="0", choices=sortChoices)
config.plugins.InfoBarTimers.endedOverlay = ConfigSelectionNumber(default=3, min=0, max=10, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.endedShow = ConfigSelectionNumber(default=10, min=-1, max=100, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.waitingOverlay = ConfigSelectionNumber(default=3, min=0, max=10, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.waitingShow = ConfigSelectionNumber(default=10, min=-1, max=100, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.disabledOverlay = ConfigSelectionNumber(default=3, min=0, max=10, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.disabledShow = ConfigSelectionNumber(default=10, min=-1, max=100, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.format = ConfigSelection(default="0", choices=formatChoices)
config.plugins.InfoBarTimers.signalIndex = ConfigSelection(default="1", choices=signalChoices)
config.plugins.InfoBarTimers.separatorIndex  = ConfigSelection(default="1", choices=separatorChoices)
config.plugins.InfoBarTimers.position = ConfigSequence(default=overlayPositions.get(desktopHeight, [50, 140]), seperator=",", limits=[(0, desktopWidth), (0, desktopHeight)])
config.plugins.InfoBarTimers.style = ConfigSelection(default="default", choices=styleChoices)
config.plugins.InfoBarTimers.entries = ConfigSelectionNumber(default=DEF_ENTRIES, min=MIN_ENTRIES, max=DEF_ENTRIES, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.refreshOverlay = ConfigSelectionNumber(default=0, min=0, max=60, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.refreshShow = ConfigSelectionNumber(default=10, min=0, max=60, stepwidth=1, wraparound=True)
config.plugins.InfoBarTimers.showOverlayList = ConfigYesNo(default=False)


class InfoBarTimersSetup(Setup):
	def __init__(self, session):
		Setup.__init__(self, session=session, setup="InfoBarTimers", plugin="Extensions/InfoBarTimers")
		config.plugins.InfoBarTimers.style.addNotifier(self.updateLayout, initial_call=False, immediate_feedback=True)
		self.updateLayout(None)
		# if self.cleanUp not in self.onClose:
		self.onClose.append(self.cleanUp)

	def updateLayout(self, configElement):
		entries, defEntries, minEntries, maxEntries = InfoBarTimersOverlay.overlay.getEntries()
		config.plugins.InfoBarTimers.entries.setChoices([str(x) for x in range(minEntries, maxEntries + 1)], default=str(defEntries))
		# Remove next 2 lines after testing...
		# itemHeight = InfoBarTimersOverlay.overlay.getItemHeight(config.plugins.InfoBarTimers.style.value)
		# print("[InfoBarTimers-Setup] updateLayout DEBUG: style='%s', itemHeight=%d, entries=%d, defEntries=%d, minEntries=%d, maxEntries=%d" % (config.plugins.InfoBarTimers.style.value, itemHeight, entries, defEntries, minEntries, maxEntries))

	def keySave(self):
		self.saveAll()
		# Update extension menu integration.
		if config.plugins.InfoBarTimers.extensionsShow.value:
			if pluginShow not in plugins.pluginList:
				plugins.addPlugin(pluginShow)
		else:
			if pluginShow in plugins.pluginList:
				plugins.removePlugin(pluginShow)
		if config.plugins.InfoBarTimers.extensionsSetup.value:
			if pluginSetup not in plugins.pluginList:
				plugins.addPlugin(pluginSetup)
		else:
			if pluginSetup in plugins.pluginList:
				plugins.removePlugin(pluginSetup)
		self.close()

	def cleanUp(self):
		config.plugins.InfoBarTimers.style.removeNotifier(self.updateLayout)
		# if self.cleanUp in self.onClose:
		self.onClose.remove(self.cleanUp)


# If ended or waiting is None then use the config values for the number of timer entries.
# If ended or waiting is -1 then use all available timer entries of this type.
# If ended or waiting is 0 then don't use this type of timer entry.
# If ended or waiting is > 0 then use up to this number of this type of timer entry.
#
def updateTimerList(recordTimer, ended, waiting, disabled, order, reverse):
	timersDisabled = []
	timersEnded = []
	for item in reversed(recordTimer.processed_timers):
		if item.disabled:
			if disabled:
				timersDisabled.append(item)
				disabled -= 1
		else:
			if ended:
				timersEnded.append(item)
				ended -= 1
	timersActive = []
	timersWaiting = []
	for item in recordTimer.timer_list:
		if item.state == item.StateWaiting:
			if waiting:
				timersWaiting.append(item)
				waiting -= 1
		else:
			timersActive.append(item)
	reverse = True if reverse == "1" else False
	timers = []
	for item in order:
		if item == "a":
			timersActive.sort(key=attrgetter("begin"), reverse=reverse)
			timers.extend(timersActive)
		elif item == "d":
			timersDisabled.sort(key=attrgetter("begin"), reverse=reverse)
			timers.extend(timersDisabled)
		elif item == "e":
			timersEnded.sort(key=attrgetter("begin"), reverse=reverse)
			timers.extend(timersEnded)
		elif item == "w":
			timersWaiting.sort(key=attrgetter("begin"), reverse=reverse)
			timers.extend(timersWaiting)
	return timers


def formatTimerList(timers, icons):
	snrLabels = ["", _("Q"), _("Q"), _("SNR")]
	powerLabels = ["", _("S"), _("P"), _("AGC")]
	labelSeparators = ["", " ", ":", "=", "-", ": ", " = ", " - "]
	signal = int(config.plugins.InfoBarTimers.signalIndex.value)
	if signal:
		separator = labelSeparators[int(config.plugins.InfoBarTimers.separatorIndex.value)]
	else:
		separator = ""
	list = []
	for item in timers:
		if item.state == item.StateWaiting:
			state = icons.pixmaps[ICON_WAIT]
			stateText = _("Waiting")
		elif item.state == item.StatePrepared:
			state = icons.pixmaps[ICON_PREP]
			stateText = _("Preparing")
		elif item.state == item.StateRunning:
			state = icons.pixmaps[ICON_REC]
			stateText = _("Recording")
		elif item.state == item.StateFailed:
			state = icons.pixmaps[ICON_FAIL]
			stateText = _("Failed")
		elif item.state == item.StateEnded:
			state = icons.pixmaps[ICON_END]
			stateText = _("Ended")
		else:
			state = None
			stateText = _("Unknown")
		if item.disabled:
			state = icons.pixmaps[ICON_OFF]
			stateText = _("Disabled")
		if hasattr(item, "isAutoTimer") and item.isAutoTimer:
			type = icons.pixmaps[ICON_AUTO]
			typeText = _("AutoTimer")
		elif hasattr(item, "ice_timer_id") and item.ice_timer_id:
			type = LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "icons/timer_icetv.png"))
			if not type:
				type = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "SystemPlugins/IceTV/icons/timer_icetv.png"))
			typeText = _("IceTV")
		elif item.repeated:
			type = icons.pixmaps[ICON_REP]
			typeText = _("Repeating")
		else:
			type = None
			typeText = _("Timer")
		feinfo = item.record_service and item.record_service.frontendInfo()
		data = feinfo and feinfo.getAll(False)
		if data:
			tuner = data.get("tuner_number", -1)
			tuner = chr(int(tuner) + ord("A")) if tuner is not None and tuner > -1 else None
			tunerType = data.get("tuner_type", None)
			ber = data.get("tuner_bit_error_rate", None)
			snrValue = data.get("tuner_signal_quality", None)
			if snrValue is not None:
				snrValue = int(snrValue * 100 / 65535)
				snr = "%s%s%d%%" % (snrLabels[signal], separator, snrValue)
			else:
				snrValue = -1  # Use an out-out-of range value to hide the bar graph.
				snr = None
			snr_dB = data.get("tuner_signal_quality_db", None)
			if snr_dB is not None:
				snr_dB = "%.1f" % (snr_dB / 100.0)
			powerValue = data.get("tuner_signal_power", None)
			if powerValue is not None:
				powerValue = int(powerValue * 100 / 65535)
				power = "%s%s%d%%" % (powerLabels[signal], separator, powerValue)
			else:
				powerValue = -1  # Use an out-out-of range value to hide the bar graph.
				power = None
		else:
			tuner = None
			tunerType = None
			ber = None
			snrValue = -1  # Use an out-out-of range value to hide the bar graph.
			snr = None
			snr_dB = None
			powerValue = -1  # Use an out-out-of range value to hide the bar graph.
			power = None
		picon = getPiconName(item.service_ref.ref.toString())
		if picon == "":
			servicePicon = None
		else:
			servicePicon = LoadPixmap(picon)
		serviceName = item.service_ref.getServiceName() if item.service_ref else None
		timerName = item.name if item.name else None
		prepare = "%d Secs" % item.prepare_time if item.prepare_time < 60 else "%d Mins" % (item.prepare_time / 60)
		if item.begin and item.end:
			dateFmt = config.usage.date.dayshort.value  # Set the display date format
			timeFmt = config.usage.time.short.value  # Set the display time format
			begin = strftime(dateFmt + " " + timeFmt, localtime(item.begin))
			beginDate = strftime(dateFmt, localtime(item.begin))
			beginTime = strftime(timeFmt, localtime(item.begin))
			end = strftime(dateFmt + " " + timeFmt, localtime(item.end))
			endDate = strftime(dateFmt, localtime(item.end))
			endTime = strftime(timeFmt, localtime(item.end))
			beginEnd = begin + " - " + strftime(timeFmt, localtime(item.end))
			durationValue = item.end - item.begin
			duration = formatTimeValue(durationValue)
			durationWord = "%d Secs" % durationValue if durationValue < 60 else "%d Mins" % int(durationValue / 60)
			durationHrs = None if durationValue < 0 else "%d:%02d" % (durationValue / 3600, durationValue / 60 % 60)
			durationMins = None if durationValue < 0 else "%d:%02d" % (durationValue / 60, durationValue % 60)
			durationSecs = None if durationValue < 0 else "%d:%02d:%02d" % (durationValue / 3600, durationValue / 60 % 60, durationValue % 60)
			now = time()
			if item.begin <= now <= item.end:
				if config.usage.elapsed_time_positive_osd.value:
					signElapsed = "+"
					signRemaining = "-"
				else:
					signElapsed = "-"
					signRemaining = "+"
				elapsedValue = now - item.begin
				elapsed = formatTimeValue(elapsedValue)
				elapsedWord = "%s%d Secs" % (signElapsed, elapsedValue) if elapsedValue < 60 else "%s%d Mins" % (signElapsed, int(elapsedValue / 60))
				elapsedHrs = None if elapsedValue < 0 else "%s%d:%02d" % (signElapsed, elapsedValue / 3600, elapsedValue / 60 % 60)
				elapsedMins = None if elapsedValue < 0 else "%s%d:%02d" % (signElapsed, elapsedValue / 60, elapsedValue % 60)
				elapsedSecs = None if elapsedValue < 0 else "%s%d:%02d:%02d" % (signElapsed, elapsedValue / 3600, elapsedValue / 60 % 60, elapsedValue % 60)
				remainingValue = item.end - now
				remaining = formatTimeValue(remainingValue)
				remainingWord = "%s%d Secs" % (signRemaining, remainingValue) if remainingValue < 60 else "%s%d Mins" % (signRemaining, int(remainingValue / 60))
				remainingHrs = None if remainingValue < 0 else "%s%d:%02d" % (signRemaining, remainingValue / 3600, remainingValue / 60 % 60)
				remainingMins = None if remainingValue < 0 else "%s%d:%02d" % (signRemaining, remainingValue / 60, remainingValue % 60)
				remainingSecs = None if remainingValue < 0 else "%s%d:%02d:%02d" % (signRemaining, remainingValue / 3600, remainingValue / 60 % 60, remainingValue % 60)
				format = config.usage.swap_time_remaining_on_osd.value
				if format == "0":
					elapsedRemaining = "%s%d Secs" % (signRemaining, remainingValue) if remainingValue < 60 else "%s%d Mins" % (signRemaining, int(remainingValue / 60))
				elif format == "1":
					elapsedRemaining = "%s%d Secs" % (signElapsed, elapsedValue) if elapsedValue < 60 else "%s%d Mins" % (signElapsed, int(elapsedValue / 60))
				elif format == "2":
					elapsedRemaining = "%s%d %s%d Mins" % (signElapsed, int(elapsedValue / 60), signRemaining, int(remainingValue / 60))
				elif format == "3":
					elapsedRemaining = "%s%d %s%d Mins" % (signRemaining, int(remainingValue / 60), signElapsed, int(elapsedValue / 60))
				else:
					print("[InfoBarTimers] Error: config.usage.swap_time_remaining_on_osd value is not within expected range!! (Value=%s)" % config.usage.swap_time_remaining_on_osd.value)
					elapsedRemaining = None
				progressValue = int(elapsedValue / durationValue * 100.0)
				if progressValue < 0:
					progressValue = 0
				elif progressValue > 100:
					progressValue = 100
				progress = "%d%%" % progressValue
			else:
				elapsed = None
				elapsedWord = None
				elapsedHrs = None
				elapsedMins = None
				elapsedSecs = None
				remaining = None
				remainingWord = None
				remainingHrs = None
				remainingMins = None
				remainingSecs = None
				elapsedRemaining = None
				progressValue = -1  # Use an out-out-of range value to hide the bar graph.
				progress = None
		else:
			begin = None
			beginDate = None
			beginTime = None
			end = None
			endDate = None
			endTime = None
			beginEnd = None
			duration = None
			durationWord = None
			durationHrs = None
			durationMins = None
			durationSecs = None
			elapsed = None
			elapsedWord = None
			elapsedHrs = None
			elapsedMins = None
			elapsedSecs = None
			remaining = None
			remainingWord = None
			remainingHrs = None
			remainingMins = None
			remainingSecs = None
			elapsedRemaining = None
			progressValue = -1  # Use an out-out-of range value to hide the bar graph
			progress = None
		tags = "'%s'" % "', '".join(item.tags) if item.tags else None
		description = item.description if item.description else None
		dirName = item.dirname if item.dirname else None  # Custom directory
		list.append(
			(state, stateText, type, typeText, tuner, tunerType, ber, snrValue, snr, snr_dB, powerValue, power,
			servicePicon, serviceName, timerName, prepare, begin, beginDate, beginTime, end, endDate, endTime, beginEnd,
			duration, durationWord, durationHrs, durationMins, durationSecs, elapsed, elapsedWord, elapsedHrs, elapsedMins, elapsedSecs,
			remaining, remainingWord, remainingHrs, remainingMins, remainingSecs, elapsedRemaining, progressValue, progress,
			tags, description, dirName)
		)
	return list


def formatTimeValue(value):
	if config.plugins.InfoBarTimers.format.value == "1":
		format = None if value < 0 else "%d:%02d:%02d" % (value / 3600, value / 60 % 60, value % 60)
	elif config.plugins.InfoBarTimers.format.value == "2":
		format = None if value < 0 else "%d:%02d" % (value / 60, value % 60)
	elif config.plugins.InfoBarTimers.format.value == "3":
		format = None if value < 0 else "%d:%02d" % (value / 3600, value / 60 % 60)
	else:
		format = "%d Secs" % value if value < 60 else "%d Mins" % int(value / 60)
	return format


# Template fields:
# 	 0 -> Image, taken from "Icons" list above, that represents the state of the timer (Waiting, Preparing, Running or Ended)
# 	 1 -> Text message representation of field 0
# 	 2 -> Image, taken from "Icons" list above, that represents the type of timer (AutoTimer, IceTV, Repeating)
# 	 3 -> Text message representation of field 2
# 	 4 -> Tuner letter of tuner being used for a running timer (A, B, C, ...)
# 	 5 -> Tuner type of tuner being used for a running timer (DVB-C, DVB-S, DVB-T, ...)
# 	 6 -> Tuner Bit Error Rate of tuner being used for a running timer
# 	 7 -> Tuner Signal to Noise Ratio of tuner being used for a running timer to be used for a bar graph type display
# 	 8 -> Tuner Signal to Noise Ratio of tuner being used for a running timer in percentage format
# 	 9 -> Tuner Signal to Noise Ratio (in dB) of tuner being used for a running timer
# 	10 -> Tuner signal power of tuner being used for a running timer to be used for a bar graph type display
# 	11 -> Tuner signal power of tuner being used for a running timer in percentage format
# 	12 -> Service picon for the timer
# 	13 -> Service name for the timer
# 	14 -> Timer name for the timer
# 	15 -> Prepare time for the timer
# 	16 -> Begin date and time for the timer (includes padding)
# 	17 -> Begin date for the timer (includes padding)
# 	18 -> Begin time for the timer (includes padding)
# 	19 -> End date and time for the timer (includes padding)
# 	20 -> End date for the timer (includes padding)
# 	21 -> End time for the timer (includes padding)
# 	22 -> Begin date, time, separator " - " and end time for the timer (includes padding)
# 	23 -> Duration of the timer shown in the user selected format
# 	24 -> Duration of the timer shown in minutes based text string (eg "65 Mins")
# 	25 -> Duration of the timer shown in hours based clock format (eg "1:05")
# 	26 -> Duration of the timer shown in minutes based clock format (eg "1:05")
# 	27 -> Duration of the timer shown in seconds based clock format (eg "1:05:08")
# 	28 -> Elapsed time of a running timer shown in the user selected format
# 	29 -> Elapsed time of a running timer in minutes based test string (eg "25 Mins")
# 	30 -> Elapsed of the timer shown in hours based clock format (eg "0:25")
# 	31 -> Elapsed of the timer shown in minutes based clock format (eg "0:25")
# 	32 -> Elapsed of the timer shown in seconds based clock format (eg "0:25:08")
# 	33 -> Remaining time of a running timer shown in the user selected format
# 	34 -> Remaining time of a running timer in minutes based text string (eg "40 Mins")
# 	35 -> Remaining of the timer shown in hours based clock format (eg "0:40")
# 	36 -> Remaining of the timer shown in minutes based clock format (eg "0:40")
# 	37 -> Remaining of the timer shown in seconds based clock format (eg "0:40:08")
# 	38 -> Elapsed / Remaining time of a running timer formatted to UI settings
# 	39 -> Progress of a running timer to be used for a bar graph type display
# 	40 -> Progress of a running timer shown as a percentage based text string (eg "68%")
# 	41 -> List of tags associated with the timer
# 	42 -> Description text associated with this timer
# 	43 -> Directory name to be used for the timer if the default is NOT being used
#
class InfoBarTimersOverlay(Screen):
	overlay = None
	skinTemplate = """
	<screen name="InfoBarTimersOverlay" title="InfoBar Timers" position="center,%d" size="%d,%d" flags="wfNoBorder" zPosition="+1">
		<widget name="Icons" position="0,0" size="%d,%d" pixmaps="icons/timer_off.png,icons/timer_wait.png,icons/timer_prep.png,icons/timer_rec.png,icons/timer_zap.png,icons/timer_failed.png,icons/timer_done.png,icons/timer_autotimer.png,icons/timer_rep.png" alphatest="blend" />
		<widget source="Timers" render="Listbox" position="center,center" size="%d,%d">
			<convert type="TemplatedMultiContent">
				{
				"templates":
					{
					"default": (%d,
						[
						MultiContentEntryPixmapAlphaBlend(pos = (0, %d), size = (%d, %d), png = 0),  # State icon
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 2),  # Type icon (AutoTimer, IceTV, Repeat)
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 4, color = "#00ff0000"),  # Tuner letter
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 12, flags = BT_SCALE),  # Service picon
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 13),  # Service name
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 14),  # Timer name
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text = 22),  # Begin - End time
						MultiContentEntryProgress(pos = (%d, %d), size = (%d, %d), percent = -39, borderWidth = 1, foreColor = "#00ff0000", backColor = "#00000000"),  # Progress bar
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text = 23)  # Duration
						]),
					"Enhanced": (%d,
						[
						MultiContentEntryPixmapAlphaBlend(pos = (0, %d), size = (%d, %d), png = 0, flags = BT_SCALE),  # State icon
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 2, flags = BT_SCALE),  # Type icon (AutoTimer, IceTV, Repeat)
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 12, flags = BT_SCALE),  # Service picon
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_LEFT | RT_VALIGN_CENTER, text = 14),  # Timer name
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 3, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP, text = 4, color = "#00ff0000"),  # Tuner letter
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 3, flags = RT_HALIGN_RIGHT | RT_VALIGN_TOP, text = 22),  # Begin - End time
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 13),  # Service name
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 11),  # Power
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 8),  # SNR
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 5),  # Tuner type
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 2, flags = RT_HALIGN_CENTER | RT_VALIGN_CENTER, text = 38),  # Elapsed / Remaining time
						MultiContentEntryProgress(pos = (%d, %d), size = (%d, %d), percent = -39, borderWidth = 1, foreColor = "#00ff0000", backColor = "#00000000"),  # Progress bar
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text = 23),  # Duration
						]),
					"Enhanced (Alt)": (%d,
						[
						MultiContentEntryPixmapAlphaBlend(pos = (0, %d), size = (%d, %d), png = 0, flags = BT_SCALE),  # State icon
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 2, flags = BT_SCALE),  # Type icon (AutoTimer, IceTV, Repeat)
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 12, flags = BT_SCALE),  # Service picon
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 3, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP, text = 14),  # Timer name
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 13),  # Service name
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 4, color = "#00ff0000"),  # Tuner letter
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 11),  # Power
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 8),  # SNR
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 3, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 5),  # Tuner type
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text = 22),  # Begin - End time
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 2, flags = RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text = 38),  # Elapsed / Remaining time
						MultiContentEntryProgress(pos = (%d, %d), size = (%d, %d), percent = -39, borderWidth = 1, foreColor = "#00ff0000", backColor = "#00000000"),  # Progress bar
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_RIGHT | RT_VALIGN_CENTER, text = 23),  # Duration
						]),
					"Detailed": (%d,
						[
						MultiContentEntryPixmapAlphaBlend(pos = (0, %d), size = (%d, %d), png = 0, flags = BT_SCALE),  # State icon
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 2, flags = BT_SCALE),  # Type icon (AutoTimer, IceTV, Repeat)
						MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 12, flags = BT_SCALE),  # Service picon
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP, text = 14),  # Timer name
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 13),  # Service name
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 4, color = "#00ff0000"),  # Tuner letter
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 11),  # Power
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 8),  # SNR
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 5),  # Tuner type
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_CENTER | RT_VALIGN_TOP, text = 22),  # Begin - End time
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 28),  # Elapsed time
						MultiContentEntryProgress(pos = (%d, %d), size = (%d, %d), percent = -39, borderWidth = 1, foreColor = "#00ff0000", backColor = "#00000000"),  # Progress bar
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 33),  # Remaining time
						MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_RIGHT | RT_VALIGN_TOP, text = 23),  # Duration
						MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 40)  # Progress percentage
						])
					},
				"fonts": [parseFont("Regular;%d"), parseFont("Regular;%d"), parseFont("Regular;%d"), parseFont("Regular;%d")],
				"scrollbarMode": "showNever",
				"selectionEnabled": False
				}
			</convert>
		</widget>
	</screen>"""
	scaleData = [
		140, 1180, 420,
		20, 20,
		1160, 400,
		25,
		2, 20, 20,
		25, 2, 20, 20,
		50, 20, 25,
		70, 1, 40, 24,
		120, 150, 25,
		280, 340, 25,
		630, 360, 25,
		1000, 8, 50, 9,
		1060, 100, 25,
		30,
		5, 20, 20,
		25, 5, 20, 20,
		50, 1, 47, 28,
		110, 390, 30,
		510, 20, 15,
		540, 330, 15,
		510, 15, 120, 15,
		640, 15, 80, 15,
		730, 15, 80, 15,
		820, 15, 80, 15,
		910, 140, 20,
		910, 20, 140, 6,
		1060, 100, 30,
		30,
		5, 20, 20,
		25, 5, 20, 20,
		50, 1, 47, 28,
		110, 450, 15,
		120, 15, 140, 15,
		270, 15, 20, 15,
		300, 15, 80, 15,
		390, 15, 80, 15,
		480, 15, 80, 15,
		570, 330, 30,
		910, 140, 18,
		910, 20, 140, 6,
		1060, 100, 30,
		40,
		10, 20, 20,
		25, 10, 20, 20,
		55, 1, 63, 38,
		130, 540, 23,
		150, 23, 220, 17,
		380, 23, 20, 17,
		410, 23, 80, 17,
		500, 23, 80, 17,
		590, 23, 80, 17,
		680, 370, 23,
		680, 23, 100, 17,
		790, 28, 150, 7,
		950, 23, 100, 17,
		1060, 100, 23,
		1060, 23, 100, 17,
		20, 15, 17, 13
	]
	skin = None

	def __init__(self, session):
		Screen.__init__(self, session)
		minRes = 720
		height = max(minRes, desktopHeight)
		InfoBarTimersOverlay.skin = InfoBarTimersOverlay.skinTemplate % tuple([x * height / minRes for x in InfoBarTimersOverlay.scaleData])
		# print("[InfoBarTimers] DEBUG: Height=%d\n%s" % (height, InfoBarTimersOverlay.skin))
		self["Icons"] = MultiPixmap()
		self["Icons"].hide()
		self["Timers"] = List()
		self.overlayWidth = 0
		self.timersWidth = 0
		self.timersHeight = 0
		self.heightPadding = 0
		self.displayed = False
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.refreshTimerList)
		if self.layoutFinish not in self.onLayoutFinish:
			self.onLayoutFinish.append(self.layoutFinish)
		if self.refreshTimerList not in self.session.nav.RecordTimer.on_state_change:
			self.session.nav.RecordTimer.on_state_change.append(self.refreshTimerList)
		if self.cleanUp not in self.onClose:
			self.onClose.append(self.cleanUp)
		InfoBarTimersOverlay.overlay = self

	def layoutFinish(self):
		if not self.getTitle():
			self.setTitle(_("InfoBar Timers"))
		self.overlayWidth = self.instance.size().width()
		self.timersWidth = self["Timers"].downstream_elements[0].downstream_elements[0].instance.size().width()
		self.timersHeight = self["Timers"].downstream_elements[0].downstream_elements[0].instance.size().height()
		yOffset = self["Timers"].downstream_elements[0].downstream_elements[0].instance.position().y()
		yPadding = self.instance.size().height() - self.timersHeight - yOffset
		self.heightPadding = yOffset + yPadding
		styles = None
		if "templates" in self["Timers"].downstream_elements[0].template:
			styles = sorted(self["Timers"].downstream_elements[0].template["templates"].keys())
			if styles:
				config.plugins.InfoBarTimers.style.setChoices([(item, "%s%s" % (item[:1].upper(), item[1:])) for item in styles], default="default")
		config.plugins.InfoBarTimers.style.value = config.plugins.InfoBarTimers.style.saved_value
		self["Timers"].downstream_elements[0].downstream_elements[0].instance.setSelectionEnable(0)
		# Remove next line after testing...
		# print("[InfoBarTimers-Overlay] layoutFinish DEBUG: Screen style='%s', styles='%s', overlayWidth=%d, timersWidth=%d, timersHeight=%d, yOffset=%d, yPadding=%d" % (config.plugins.InfoBarTimers.style.value, str(styles), self.overlayWidth, self.timersWidth, self.timersHeight, yOffset, yPadding))

	def getActiveStyle(self):
		savedStyle = config.plugins.InfoBarTimers.style.value
		if savedStyle:
			self["Timers"].setStyle(savedStyle)
		style = self["Timers"].getStyle()
		return style

	def getItemHeight(self, style):
		if "templates" in self["Timers"].downstream_elements[0].template:
			itemHeight = self["Timers"].downstream_elements[0].template["templates"].get(style, None)[0]
		else:
			itemHeight = self["Timers"].downstream_elements[0].template.get("itemHeight", None)
		if itemHeight is None or type(itemHeight) is not int:
			itemHeight = DEF_ITEMHEIGHT
			print("[InfoBarTimers] Error: No itemHeight found!  Assuming a default of %d." % itemHeight)
		return itemHeight

	def getEntries(self):
		entries = int(config.plugins.InfoBarTimers.entries.value)
		maxEntries = int(self.timersHeight / self.getItemHeight(self.getActiveStyle()))
		if entries > maxEntries:
			config.plugins.InfoBarTimers.entries.value = str(maxEntries)
			config.plugins.InfoBarTimers.entries.save()
			entries = maxEntries
		defEntries = DEF_ENTRIES
		if defEntries > entries:
			defEntries = entries
		minEntries = MIN_ENTRIES
		if minEntries > entries:
			minEntries = entries
		# Remove next line after testing...
		# print("[InfoBarTimers-Overlay] getEntries DEBUG: entries=%d, defEntries=%d, minEntries=%d, maxEntries=%d" % (entries, defEntries, minEntries, maxEntries))
		return entries, defEntries, minEntries, maxEntries

	def refreshTimerList(self, entry=None):
		self.refreshTimer.stop()
		if config.plugins.InfoBarTimers.enabled.value:
			default = overlayPositions.get(desktopHeight, [50, 140])
			left, top = config.plugins.InfoBarTimers.position.value
			if left >= desktopWidth:
				left = default[0]
			if top >= desktopHeight:
				top = default[1]
			self.instance.move(ePoint(left, top))
			# self.instance.setZPosition(config.plugins.InfoBarTimers.zPosition.value)
			entries, defEntries, minEntries, maxEntries = self.getEntries()
			ended = config.plugins.InfoBarTimers.endedOverlay.value
			waiting = config.plugins.InfoBarTimers.waitingOverlay.value
			disabled = config.plugins.InfoBarTimers.disabledOverlay.value
			order = config.plugins.InfoBarTimers.orderOverlay.value
			reverse = config.plugins.InfoBarTimers.sortOverlay.value
			timers = updateTimerList(self.session.nav.RecordTimer, ended=ended, waiting=waiting, disabled=disabled, order=order, reverse=reverse)
			limit = len(timers)
			if limit > entries:
				diff = limit - entries
				while diff:
					if disabled:
						disabled -= 1
						diff -= 1
						if diff == 0:
							break
					if ended:
						ended -= 1
						diff -= 1
						if diff == 0:
							break
					if waiting:
						waiting -= 1
						diff -= 1
						if diff == 0:
							break
					if disabled + ended + waiting == 0:
						print("[InfoBarTimers] Error: Timer list is too long to be fully displayed! (List=%d, Entries=%d)" % (limit, entries))
						break
				timers = updateTimerList(self.session.nav.RecordTimer, ended=ended, waiting=waiting, disabled=disabled, order=order, reverse=reverse)
				limit = len(timers)
				if limit > entries:
					limit = entries
			itemHeight = self.getItemHeight(self.getActiveStyle())
			height = limit * itemHeight
			self.instance.resize(eSize(self.overlayWidth, height + self.heightPadding))
			self["Timers"].downstream_elements[0].downstream_elements[0].instance.resize(eSize(self.timersWidth, height))
			# Remove next line after testing...
			# print("[InfoBarTimers-Overlay] refreshTimerList DEBUG: Screen pos=(%d, %d), size=(%d, %d) - Timers size=(%d, %d), itemHeight=%d - Entries=%d, defEntries=%d, minEntries=%d, maxEntries=%d" % (left, top, self.overlayWidth, height + self.heightPadding, self.timersWidth, height, itemHeight, limit, defEntries, minEntries, maxEntries))
			self["Timers"].updateList(formatTimerList(timers, self["Icons"]))
			if self.displayed and config.plugins.InfoBarTimers.refreshOverlay.value:
				self.refreshTimer.startLongTimer(config.plugins.InfoBarTimers.refreshOverlay.value)

	def processDisplay(self, state):
		if config.plugins.InfoBarTimers.enabled.value:
			self.displayed = state
			if state:
				self.refreshTimerList()
				if self["Timers"].list:
					self.show()
			else:
				self.refreshTimer.stop()
				self.hide()

	def cleanUp(self):
		self.refreshTimer.stop()
		if self.layoutFinish in self.onLayoutFinish:
			self.onLayoutFinish.remove(self.layoutFinish)
		if self.refreshTimerList in self.session.nav.RecordTimer.on_state_change:
			self.session.nav.RecordTimer.on_state_change.remove(self.refreshTimerList)
		if self.cleanUp in self.onClose:
			self.onClose.remove(self.cleanUp)
		InfoBarTimersOverlay.overlay = None


# Template fields are as above.
#
class InfoBarTimersShow(Screen, HelpableScreen):
	skinTemplate = """
	<screen name="InfoBarTimersShow" title="Show Timers" position="fill" flags="wfNoBorder">
		<widget name="Icons" position="0,0" size="%d,%d" pixmaps="icons/timer_off.png,icons/timer_wait.png,icons/timer_prep.png,icons/timer_rec.png,icons/timer_zap.png,icons/timer_failed.png,icons/timer_done.png,icons/timer_autotimer.png,icons/timer_rep.png" alphatest="blend" />
		<widget source="Timers" render="Listbox" position="center,%d" size="%d,%d">
			<convert type="TemplatedMultiContent">
				{
				"template":
					[
					MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 0, flags = BT_SCALE),  # State icon
					MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 2, flags = BT_SCALE),  # Type icon (AutoTimer, IceTV, Repeat)
					MultiContentEntryPixmapAlphaBlend(pos = (%d, %d), size = (%d, %d), png = 12, flags = BT_SCALE),  # Service picon
					MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_LEFT | RT_VALIGN_TOP, text = 14),  # Timer name
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 13),  # Service name
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 4, color = "#00ff0000"),  # Tuner letter
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 11),  # Power
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 8),  # SNR
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 5),  # Tuner type
					MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_CENTER | RT_VALIGN_TOP, text = 22),  # Begin - End time
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_RIGHT | RT_VALIGN_BOTTOM, text = 28),  # Elapsed time
					MultiContentEntryProgress(pos = (%d, %d), size = (%d, %d), percent = -39, borderWidth = 1, foreColor = "#00ff0000", backColor = "#00000000"),  # Progress bar
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 33),  # Remaining time
					MultiContentEntryText(pos = (%d, 0), size = (%d, %d), font = 0, flags = RT_HALIGN_RIGHT | RT_VALIGN_TOP, text = 23),  # Duration
					MultiContentEntryText(pos = (%d, %d), size = (%d, %d), font = 1, flags = RT_HALIGN_LEFT | RT_VALIGN_BOTTOM, text = 40)  # Progress percentage
					],
				"fonts": [parseFont("Regular;%d"), parseFont("Regular;%d")],
				"itemHeight": %d,
				"scrollbarMode": "showOnDemand",
				"selectionEnabled": True
				}
			</convert>
		</widget>
	</screen>"""
	scaleData = [
		20, 20,
		80, 1180, 520,
		10, 10, 20, 20,
		35, 10, 20, 20,
		65, 1, 63, 38,
		140, 530, 23,
		160, 23, 150, 17,
		320, 23, 20, 17,
		350, 23, 100, 17,
		460, 23, 100, 17,
		570, 23, 100, 17,
		680, 370, 23,
		680, 23, 100, 17,
		790, 28, 150, 7,
		950, 23, 100, 17,
		1060, 100, 23,
		1060, 23, 100, 17,
		20, 15,
		40
	]
	skin = None

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.session = session
		minRes = 720
		height = max(minRes, desktopHeight)
		InfoBarTimersShow.skin = InfoBarTimersShow.skinTemplate % tuple([x * height / minRes for x in InfoBarTimersShow.scaleData])
		# print("[InfoBarTimers] DEBUG: Height=%d\n%s" % (height, InfoBarTimersShow.skin))
		self["Actions"] = HelpableActionMap(self, ["OkCancelActions"], {
			"ok": (self.close, _("Exit InfoBarTimers")),
			"cancel": (self.close, _("Exit InfoBarTimers")),
		}, prio=0, description=_("InfoBarTimers Commands"))
		self["Icons"] = MultiPixmap()
		self["Icons"].hide()
		self["Timers"] = List()
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.refreshTimerList)
		if self.layoutFinish not in self.onLayoutFinish:
			self.onLayoutFinish.append(self.layoutFinish)
		if self.refreshTimerList not in self.session.nav.RecordTimer.on_state_change:
			self.session.nav.RecordTimer.on_state_change.append(self.refreshTimerList)
		if self.cleanUp not in self.onClose:
			self.onClose.append(self.cleanUp)

	def layoutFinish(self):
		if not self.getTitle():
			self.setTitle(_("Show Timers"))
		self.refreshTimerList()

	def refreshTimerList(self, entry=None):
		self.refreshTimer.stop()
		if config.plugins.InfoBarTimers.showOverlayList.value:
			ended = config.plugins.InfoBarTimers.endedOverlay.value
			waiting = config.plugins.InfoBarTimers.waitingOverlay.value
			disabled = config.plugins.InfoBarTimers.disabledOverlay.value
		else:
			ended = config.plugins.InfoBarTimers.endedShow.value
			waiting = config.plugins.InfoBarTimers.waitingShow.value
			disabled = config.plugins.InfoBarTimers.disabledShow.value
		order = config.plugins.InfoBarTimers.orderShow.value
		reverse = config.plugins.InfoBarTimers.sortShow.value
		self["Timers"].updateList(formatTimerList(updateTimerList(self.session.nav.RecordTimer, ended=ended, waiting=waiting, disabled=disabled, order=order, reverse=reverse), self["Icons"]))
		if config.plugins.InfoBarTimers.refreshShow.value:
			self.refreshTimer.startLongTimer(config.plugins.InfoBarTimers.refreshShow.value)

	def cleanUp(self):
		if config.plugins.InfoBarTimers.refreshShow.value:
			self.refreshTimer.stop()
		if self.layoutFinish in self.onLayoutFinish:
			self.onLayoutFinish.remove(self.layoutFinish)
		if self.refreshTimerList in self.session.nav.RecordTimer.on_state_change:
			self.session.nav.RecordTimer.on_state_change.remove(self.refreshTimerList)
		if self.cleanUp in self.onClose:
			self.onClose.remove(self.cleanUp)


def replacedInfoBarShowHide__init__(self):
	global InfoBarShowHide__init__
	InfoBarShowHide__init__(self)
	if isStandardInfoBar(self) or isMoviePlayerInfoBar(self) and config.plugins.InfoBarTimers.moviePlayer.value:
		if isStandardInfoBar(self):
			print("[InfoBarTimers] Hooking into InfoBar notifier.")
		if isMoviePlayerInfoBar(self):
			print("[InfoBarTimers] Hooking into MoviePlayer InfoBar notifier.")
		self.connectShowHideNotifier(InfoBarTimersOverlay.overlay.processDisplay)


# The detachInfoBarShowHide__init__ code is unused because WHERE_SESSIONSTART
# plugins never get called with reason == 1
#
def restoredInfoBarShowHide__init__():
	global InfoBarShowHide__init__
	if InfoBarShowHide__init__ is not None:
		InfoBarShowHide.__init__ = InfoBarShowHide__init__
		InfoBarShowHide__init__ = None


def setup(session, **kwargs):
	# try:
	session.open(InfoBarTimersSetup)
	# except Exception as err:
	# 	print("[InfoBarTimers] Setup exception '%s'." % str(err))


# Start setup from extension menu. Needs to be a different function so
# that addition/removal of plugins works in InfoBarTimersSetup, because
# equality in PluginDescriptors is tested ONLY on their fnc value.
#
def extSetup(session, **kwargs):
	setup(session, **kwargs)


def extShow(session, **kwargs):
	# try:
	session.open(InfoBarTimersShow)
	# except Exception as err:
	# 	print("[InfoBarTimers] Show exception '%s'." % str(err))


def main(reason, session, **kwargs):
	global InfoBarShowHide__init__
	if reason == 0:  # Enigma2 starting, or plugin being enabled.
		print("[InfoBarTimers] InfoBarTimers version %s started." % VERSION)
		# try:
		session.instantiateDialog(InfoBarTimersOverlay)
		# except Exception as err:
		# 	print("[InfoBarTimers] Main exception '%s'." % str(err))
		if InfoBarShowHide__init__ is None:
			InfoBarShowHide__init__ = InfoBarShowHide.__init__
			InfoBarShowHide.__init__ = replacedInfoBarShowHide__init__
	# No "elif reason == 1" because WHERE_SESSIONSTART plugins never get
	# called with reason == 1.


pluginMain = PluginDescriptor(name=NAME, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=main, needsRestart=False)
pluginShow = PluginDescriptor(name=SHOW, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], description=SHOW, icon="plugin.png", fnc=extShow, needsRestart=False)
pluginSetup = PluginDescriptor(name=SETUP, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], description=SETUP, icon="plugin.png", fnc=extSetup, needsRestart=False)
pluginMenu = PluginDescriptor(name=NAME, where=[PluginDescriptor.WHERE_PLUGINMENU], description="%s %s %s" % (NAME, _("version"), VERSION), icon="plugin.png", fnc=setup, needsRestart=False)


def Plugins(**kwargs):
	plugin = []
	plugin.append(pluginMain)
	if config.plugins.InfoBarTimers.extensionsShow.value:
		plugin.append(pluginShow)
	if config.plugins.InfoBarTimers.extensionsSetup.value:
		plugin.append(pluginSetup)
	plugin.append(pluginMenu)
	return plugin
