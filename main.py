#!/usr/bin/python

import subprocess, curses, string, math, sys, os
from time import sleep

def setStatus(text):
	global rows
	win.addstr(rows-1, 0, text)

def refreshConsoleSize():
	"""
	Recalculate variables which deal with console size
	"""
	global items_per_win, rows, cols

	rows, cols = win.getmaxyx()

	# exclude header and footer
	items_per_win = rows - 2

	redraw()


def loadData(dirpath):
	"""
	Process dirpath and return list of folders/sizes
	"""
	p = subprocess.Popen(["du", dirpath], stdout=subprocess.PIPE);
	results = p.stdout.read();
	p.stdout.close()

	lines = results.strip("\n").split("\n")[:-1]
	dirpath_len = len(dirpath);
	flist = {}
	total = 0

	for line in lines:
		size, path = line.split("\t")
		parts = path[dirpath_len:].split("/")
		if len(parts) == 1:
			flist[parts[0]] = int(size)
			total += int(size)

	data = [[".", total]]
	for path, size in sorted(flist.iteritems(), key=lambda (k,v): (v,k), reverse=True):
		data.append([path, size])
	return data

def hsize(kb):
	"""
	Return human readable filesize with suffix M, G, T or none
	Size must be passed as kb
	"""
	if kb >= 1073741824:
		return str(round(kb/1073741824, 1))+"T"
	elif kb >= 1048576:
		return str(round(kb/1048576, 1))+"G"
	if kb >= 1024:
		return str(round(kb/1024, 1))+"M"
	else:
		return str(kb)+"K"

def meter(percents, w = 22):
	"""
	Return progress bar like this: [+++++++---]
	Specified width includes "[" and "]"
	"""
	if percents < 0:
		percents = 0
	elif percents > 100:
		percents = 100
	cnt = int(round(percents * (w-2) / 100))
	return "[" + "+"*cnt + "-"*(w-2-cnt) + "]"

def endApp():
	"""
	Exit gracefully
	"""
	curses.nocbreak()
	win.keypad(0)
	curses.echo()
	curses.endwin()

def redraw():
	global cols, rows, flist, current_path
	win.erase()

	col1w = 9
	col2w = cols - col1w - 32
	col3w = 32

	col1x = 0
	col2x = col1w;
	col3x = cols-col3w

	# header
	y = 0
	win.addstr(y, col1x, "SIZE".ljust(col1w, ' '), curses.color_pair(2))
	win.addstr(y, col2x, ("PATH: "+current_path).ljust(col2w+col3w, ' '), curses.color_pair(2))

	total = flist[0][1]

	page = int(math.ceil(absy / items_per_win))
	rely = absy - (page * items_per_win)

	pos1 = (page * items_per_win)
	pos2 = pos1 + items_per_win

	for i, item in enumerate(flist[pos1:pos2]):
		y += 1

		path = item[0]
		size = item[1]

		if (y-1 == rely):
			color = curses.color_pair(3)
		else:
			color = curses.color_pair(1)

		win.addstr(y, col1x, string.ljust(hsize(size), col1w, ' '), color)
		win.addstr(y, col2x, string.ljust(path, col2w, ' '), color) # todo: strip path if too long
		if total == 0:
			percents = 0
		else:
			percents = 1.0 * size / total * 100
		win.addstr(y, col3x, string.ljust(meter(percents, col3w), col3w, ' '), color)

	# footer
	y += 1
	if y == rows-1 and absy < items_cnt-1:
		win.addstr(y, 0, "...")

	win.refresh()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

try:
	path = sys.argv[1]
except:
	path = None

if path != None:
	current_path = path
else:
	current_path = os.getcwd().rstrip("/")+"/"

print "Crunching data...",
flist = loadData(current_path)
items_cnt = len(flist)

# init curses library
win = curses.initscr()

# init colors
curses.start_color()

# enable arrow keys
win.keypad(1)

# hide cursor
curses.curs_set(0)

# read keys instantaneously
curses.cbreak()

# do not print stuff when key is presses
curses.noecho()

# define colors
curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)

# declare and then set some min/max variables
items_per_win = 0
rows, cols = 0, 0
absy, pady = 0, 0
refreshConsoleSize()

while (True):
	key = win.getch()

	#sleep(0.1)

	if (key != -1):

		# console is being resized
		if (key == curses.KEY_RESIZE):
			refreshConsoleSize()

		# up key
		elif (key == curses.KEY_UP):
			if absy == 0:
				continue
			absy -= 1
			redraw()

		# down key
		elif (key == curses.KEY_DOWN):
			if absy == items_cnt-1:
				continue
			absy += 1
			redraw()

		# page up
		elif (key == curses.KEY_PPAGE):
			absy -= items_per_win
			if absy < 0:
				absy = 0
			redraw()

		# page down
		elif (key == curses.KEY_NPAGE):
			absy += items_per_win
			if absy > items_cnt-1:
				absy = items_cnt-1
			redraw()

		# enter
		elif (key == 10):
			if absy == 0:
				continue
			setStatus("Loading...")
			win.refresh()
			current_path += flist[absy][0]+"/"

			flist = loadData(current_path)
			items_cnt = len(flist)
			absy = 0
			redraw()

		# backspace
		elif (key == curses.KEY_BACKSPACE):
			if current_path == "/":
				continue
			setStatus("Loading...")
			win.refresh()
			parts = current_path.strip("/").split("/")
			current_path = "/"+"/".join(parts[:-1])+"/"

			flist = loadData(current_path)
			items_cnt = len(flist)
			absy = 0
			redraw()

		# escape or q
		elif (key == 27 or key == 113):
			break

endApp();