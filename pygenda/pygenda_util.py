# -*- coding: utf-8 -*-
#
# pygenda_util.py
# Miscellaneous utility functions for Pygenda.
#
# Copyright (C) 2022 Matthew Lewis
#
# This file is part of Pygenda.
#
# Pygenda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# Pygenda is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pygenda. If not, see <https://www.gnu.org/licenses/>.


from calendar import day_abbr,month_abbr
from icalendar import cal as iCal
from datetime import date, time, datetime, timedelta, tzinfo
from dateutil import tz as du_tz
import locale
from typing import Tuple

from .pygenda_config import Config


def datetime_to_date(dt:date) -> date:
	# Extract date from datetime object (which might be a date)
	try:
		return dt.date()
	except AttributeError:
		return dt


def datetime_to_time(dt:date):
	# Extract time from datetime object.
	# Return False if no time component.
	try:
		return dt.time()
	except AttributeError:
		return False


# For many repeat types, we need to have a timezone that is "aware" of
# summer time changes to make correct, e.g. hourly, calculations
# !! I'm pretty sure this will break compatibility with Windows...
# !! (Maybe use tzlocal module: https://github.com/regebro/tzlocal)
LOCAL_TZ = du_tz.tzfile('/etc/localtime')


def date_to_datetime(dt:date, tz:tzinfo=None) -> datetime:
	# Return datetime from dt argument. Set time to midnight if no time.
	# If tz parameter is not None/False, and dt has no timezone, add tz (True -> add local timezone)
	# Hence this function can be used to guarantee we have datetime with a timezone
	dt_ret= dt if isinstance(dt,datetime) else datetime(dt.year,dt.month,dt.day)
	if tz and dt_ret.tzinfo is None:
		dt_ret = dt_ret.replace(tzinfo=LOCAL_TZ if tz is True else tz)
	return dt_ret


def start_end_dts_event(event:iCal.Event) -> Tuple[date,date]:
	# Return start & end time of an event.
	# End time calculated from duration if needed; is None if no end/duration.
	start = event['DTSTART'].dt
	if 'DTEND' in event:
		end = event['DTEND'].dt
	elif 'DURATION' in event:
		end = start + event['DURATION'].dt
	else:
		end = None
	return start,end


def start_end_dts_occ(occ:Tuple[iCal.Event,date]) -> Tuple[date,date]:
	# Return start & end time of an occurrence (an (event,date[time]) pair)
	start = occ[1]
	if 'DTEND' in occ[0]:
		root_dt = occ[0]['DTSTART'].dt
		if isinstance(start, datetime):
			root_dt = date_to_datetime(root_dt,start.tzinfo)
		d = start - root_dt
		end = occ[0]['DTEND'].dt + d
	elif 'DURATION' in occ[0]:
		end = start + occ[0]['DURATION'].dt
	else:
		end = None
	return start,end


def format_time(dt, aslocal:bool=False) -> str:
	# Return time as string, formatted according to app config settings.
	# Argument 'dt' can be a time or a datetime.
	# If aslocal is True, convert time to local device time before formatting.
	if aslocal and dt.tzinfo:
		dt = dt.astimezone()
	if Config.get_bool('global','24hr'):
		fmt = '{hr:02d}{hs:s}{min:02d}'
		return fmt.format(hr=dt.hour, min=dt.minute, hs=Config.get('global','time_sep'))
	else:
		fmt = '{hr:d}{hs:s}{min:02d}{ampm:s}'
		return fmt.format(hr=(dt.hour-1)%12+1, min=dt.minute, ampm = 'pm' if dt.hour>11 else 'am', hs=Config.get('global','time_sep'))


def format_compact_time(dt, aslocal:bool=False) -> str:
	# Return time as string, according to app config settings.
	# Compact if 12hr set & minutes=0: e.g. '1pm' rather than '1:00pm'
	# Argument 'dt' can be a time or a datetime.
	# If aslocal is True, convert time to local device time before formatting.
	if aslocal and dt.tzinfo:
		dt = dt.astimezone()
	if Config.get_bool('global','24hr'):
		fmt = '{hr:02d}{hs:s}{min:02d}'
		return fmt.format(hr=dt.hour, min=dt.minute, hs=Config.get('global','time_sep'))
	else:
		if dt.minute:
			fmt = '{hr:d}{hs:s}{min:02d}{ampm:s}'
		else:
			fmt = '{hr:d}{ampm:s}'
		return fmt.format(hr=(dt.hour-1)%12+1, min=dt.minute, ampm = 'pm' if dt.hour>11 else 'am', hs=Config.get('global','time_sep'))


def format_compact_date(dt:date, show_year:bool, aslocal:bool=False) -> str:
	# Return date as string, with abbreviated day/month names.
	# If aslocal is True, convert time to local device time before formatting.
	if aslocal and isinstance(dt,datetime) and dt.tzinfo:
		dt = dt.astimezone()
	if show_year:
		fmt = '{day:s} {date:d} {mon:s}, {yr:d}'
	else:
		fmt = '{day:s} {date:d} {mon:s}'
	return fmt.format(day=day_abbr[dt.weekday()], date=dt.day, mon=month_abbr[dt.month], yr=dt.year)


def format_compact_datetime(dt:datetime, show_year:bool, aslocal:bool=False) -> str:
	# Return datetime as string, with abbreviated day/month names, compact time.
	# If aslocal is True, convert time to local device time before formatting.
	if aslocal and isinstance(dt,datetime) and dt.tzinfo:
		dt = dt.astimezone()
	if show_year:
		fmt = '{day:s} {date:d} {mon:s}, {yr:d}, {tm:s}'
	else:
		fmt = '{day:s} {date:d} {mon:s}, {tm:s}'
	return fmt.format(day=day_abbr[dt.weekday()], date=dt.day, mon=month_abbr[dt.month], yr=dt.year, tm=format_compact_time(dt))


def day_in_week(dt:date) -> int:
	# Return the day number of dt in the week
	# Depends on config setting global/start_week_day
	day = dt.weekday()
	start_day = Config.get_int('global', 'start_week_day')
	return (day-start_day)%7


def start_of_week(dt:date) -> int:
	# Return first day of week containing dt
	# Depends on config setting global/start_week_day
	return dt - timedelta(days=day_in_week(dt))


def dt_lte(dt_a:date, dt_b:date) -> bool:
	# Return True if dt_a <= dt_b
	# dt_a and dt_b can be dates/datetimes independently
	return _dt_lte_common(dt_a, dt_b, True)


def dt_lt(dt_a:date, dt_b:date) -> bool:
	# Return True if dt_a < dt_b
	# dt_a and dt_b can be dates/datetimes independently
	return _dt_lte_common(dt_a, dt_b, False)


def _dt_lte_common(dt_a:date, dt_b:date, equality:bool) -> bool:
	# If one has timezone info, both need it for comparison
	try:
		if dt_a.tzinfo is None:
			if dt_b.tzinfo is not None:
				dt_a = dt_a.replace(tzinfo=dt_b.tzinfo)
		else:
			if dt_b.tzinfo is None:
				dt_b = dt_b.replace(tzinfo=dt_a.tzinfo)
	except AttributeError:
		pass
 
	# Now compare
	try:
		# These will succeed if both are dates or both are datetime
		if equality:
			return dt_a <= dt_b 
		else:
			return dt_a < dt_b
	except TypeError:
		try:
			eq = (dt_a == dt_b.date()) # try a is date
			# If eq then a is *start* of day when b occurs
			return eq or (dt_a < dt_b.date())
		except AttributeError:
			eq = (dt_a.date() == dt_b) # so b is date
			# If eq then b is *start* of day when a occurs
			return False if eq else (dt_a.date() < dt_b)
	return False # shouldn't reach here


# We want to be able to sort events/todos by datetime
def _entry_lt(self, other) -> bool:
	# Return True if start date/time of self < start date/time of other
	return dt_lt(self['DTSTART'].dt,other['DTSTART'].dt)

# Attach method to classes so it can be used to sort
iCal.Event.__lt__ = _entry_lt
iCal.Todo.__lt__ = _entry_lt


def guess_date_ord_from_locale() -> str:
	# Try to divine order of date (day/mon/yr mon/day/yr etc.) from locale.
	# Return a string like 'DMY' 'MDY' etc.
	dfmt = locale.nl_langinfo(locale.D_FMT) # E.g. '%x', '%m/%d/%Y'
	# To cope with dfmt=='%x': format a time & look at result
	st = date(year=3333,month=11,day=22).strftime(dfmt)
	ret = ''
	for ch in st:
		if ch=='3':
			if not ret or ret[-1]!='Y':
				ret += 'Y'
		elif ch=='1':
			if not ret or ret[-1]!='M':
				ret += 'M'
		elif ch=='2':
			if not ret or ret[-1]!='D':
				ret += 'D'
	return ret if len(ret)==3 else 'YMD'


def guess_date_sep_from_locale() -> str:
	# Try to divine date separator (/, -, etc.) from locale.
	dfmt = locale.nl_langinfo(locale.D_FMT)
	# To cope with dfmt=='%x': format a time & look at result
	st = date(year=1111,month=11,day=11).strftime(dfmt)
	for ch in st:
		if ch!='1':
			return ch
	return '-' # fallback


def guess_time_sep_from_locale() -> str:
	# Try to divine time separator (:, etc.) from locale.
	tfmt = locale.nl_langinfo(locale.T_FMT) # E.g. '%r', '%H:%M:%S'
	# To cope with tfmt=='%x': format a time & look at result
	st = time(hour=11,minute=11,second=11).strftime(tfmt)
	for ch in st:
		if ch!='1':
			return ch
	return ':' # fallback


def guess_date_fmt_text_from_locale() -> str:
	# Try to divine date formatting string from locale
	dtfmt = locale.nl_langinfo(locale.D_T_FMT) # includes time element
	ret = ''
	i = 0
	incl = True # including chars
	fmtch = False # formatting character
	while i < len(dtfmt):
		ch = dtfmt[i]
		if ch=='%' and not fmtch and dtfmt[i+1] in 'HIMRSTXZfklnprstz':
			incl = False # skip these until space char
		if incl:
			if fmtch and ch in 'aby':
				ch = ch.upper() # uppercase version for full day/month/year
			ret += ch
			fmtch = (ch=='%') # Boolean - next char is formatting char
		if ch==' ':
			incl = True
		i += 1
	return ret if ret else '%A, %B %-d, %Y' # fallback
