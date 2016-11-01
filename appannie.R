#!/usr/bin/R

# running average function
runavg_n = 7
runavg <- function(x, n=runavg_n) { filter(x, rep(1/n, n), sides=2) }

# create data.frame (must have a Date column called "stamp") for a given year
fullyear_start = 0
fullyear <- function(x, date_end, decreasing=F) {
	start = date_end - 3600*24*(365+runavg_n)
	year = subset(x, stamp <= date_end & stamp > start)
	ordered = year[with(year, order(stamp, decreasing=decreasing)),]
	latestyear = ifelse(length(ordered$stamp) > 0, max(ordered$stamp$year), 0)
	ordered$nday = ifelse(ordered$stamp$year < latestyear, ordered$stamp$yday, ordered$stamp$yday + 365)
	return(ordered)
}

to_file = !interactive()

for (f in Sys.glob('Numbers *.csv')) {
	
	# filename: replace "Numbers ", replace ".csv"; title: also replace " [app-id]"
	filename = sub('.csv', '', sub('Numbers\\s+', '', f))
	title = sub('\\s*\\[(\\d)+\\]', '', filename)
	
	# to PDF unless interactive
	if (to_file) {
		pdf.options(encoding='CP1250')
		pdf(file=paste(paste('Downloads', filename, Sys.Date()), 'pdf', sep='.'), width=12, height=7)
	}
	
	# read CSV and create a true date column
	d = read.csv(f)
	d$stamp = strptime(d$date, "%Y-%m-%d")
	
	# create ranges for the last 4 years; reverse order to sort by date from past to now
	latest = max(d$stamp)
	y1 = fullyear(d, latest)
	y2 = fullyear(d, latest - 3600*24*365)
	y3 = fullyear(d, latest - 3600*24*730)
	y4 = fullyear(d, latest - 3600*24*1095)
	max_d = max(y1$num_downloads, y2$num_downloads, y3$num_downloads, na.rm=T)	# ignore y4
	
	# create labels for the first entry of a month (entry from day 1 may be missing, so can't use stamp$mday == 1)
	y1$mth = strftime(y1$stamp, "%b")
	y1$prevmth = c(rep('Xxx',1),head(y1$mth,-1))
	lbl_set = y1[y1$mth != y1$prevmth,]
	
	# daily downloads
	par(mar=c(3,5,3,3))
	plot(y1$nday, y1$num_downloads, type='l', main=title, xlab=NULL, xaxt='n', ylab="downloads / day", col='cornsilk4', ylim=c(0, max_d))
	axis(1, at=lbl_set$nday, labels=lbl_set$mth)
	
	# new year marker
	abline(v=y1[y1$stamp$yday == 0,]$nday)
	
	if (nrow(y4) >= runavg_n) {
		lines(y4$nday, y4$num_downloads, col='cornsilk1')
		lines(y4$nday, runavg(y4$num_downloads), lwd=1, col='cadetblue')
	}
	if (nrow(y3) >= runavg_n) {
		lines(y3$nday, y3$num_downloads, col='cornsilk2')
		lines(y3$nday, runavg(y3$num_downloads), lwd=2, col='cornflowerblue')
	}
	if (nrow(y2) >= runavg_n) {
		lines(y2$nday, y2$num_downloads, col='cornsilk3')
		lines(y2$nday, runavg(y2$num_downloads), lwd=3, col='blue')
	}
	if (nrow(y1) >= runavg_n) {
		lines(y1$nday, runavg(y1$num_downloads), lwd=4, col='blue4')
	}
	
	# number of updates (scaled)
	max_upd = max(d$num_updates, na.rm=T)
	factor = max_upd / max_d
	lines(y1$nday, y1$num_updates / factor, lty='dotted')
	axis(4, at=c(0, max_d), labels=c(0, max_upd))
	
	# legend
	texts = c(paste(paste(min(y1$stamp$year + 1900, na.rm=T), max(y1$stamp$year + 1900, na.rm=T), sep='-'), format(sum(y1$num_downloads, na.rm=T), big.mark=','), sep=':  '))
	widths = c(4)
	styles = c('solid')
	colors = c('blue4')
	if (sum(y2$num_downloads, na.rm=T) > 0) {
		texts[2] = paste(paste(min(y2$stamp$year + 1900, na.rm=T), max(y2$stamp$year + 1900, na.rm=T), sep='-'), format(sum(y2$num_downloads, na.rm=T), big.mark=','), sep=':  ')
		widths[2] = 3
		styles[2] = 'solid'
		colors[2] = 'blue'
	}
	if (sum(y3$num_downloads, na.rm=T) > 0) {
		texts[3] = paste(paste(min(y3$stamp$year + 1900, na.rm=T), max(y3$stamp$year + 1900, na.rm=T), sep='-'), format(sum(y3$num_downloads, na.rm=T), big.mark=','), sep=':  ')
		widths[3] = 2
		styles[3] = 'solid'
		colors[3] = 'cornflowerblue'
	}
	if (sum(y4$num_downloads, na.rm=T) > 0) {
		texts[4] = paste(paste(min(y4$stamp$year + 1900, na.rm=T), max(y4$stamp$year + 1900, na.rm=T), sep='-'), format(sum(y4$num_downloads, na.rm=T), big.mark=','), sep=':  ')
		widths[4] = 2
		styles[4] = 'solid'
		colors[4] = 'cornflowerblue'
	}
	texts[length(texts)+1] = "Updates"
	widths[length(widths)+1] = 1
	styles[length(styles)+1] = 'dotted'
	colors[length(colors)+1] = 'black'
	
	legend('topleft', texts, lwd=widths, lty=styles, col=colors)
	
	if (to_file) {
		dev.off()
	}
}
