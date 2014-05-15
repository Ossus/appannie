#!/usr/bin/R

# running average function
runavg_n = 7
runavg <- function(x, n=runavg_n) { filter(x, rep(1/n, n), sides=2) }

to_file = !interactive()

for (f in Sys.glob('Numbers *.csv')) {
	n = sub('.csv', '', sub('Numbers ', '', f))
	
	# to PNG unless interactive
	if (to_file) {
		pdf(file=paste(paste('Downloads', n, Sys.Date()), 'pdf', sep='.'), width=12, height=7)
	}
	
	# read CSV and create a true date column
	d = read.csv(f)
	d$stamp = strptime(d$date, "%Y-%m-%d")
	
	# past year and year before that and the one before that
	y1 = d[(365+runavg_n):1,]
	y2 = d[(730+runavg_n):366,]
	y3 = d[(1095+runavg_n):731,]
	max_d = max(y1$num_downloads, y2$num_downloads, y3$num_downloads, na.rm=T)
	
	lbl_set = subset(y1, stamp$mday == 1)
	lbls = strftime(lbl_set$stamp, "%b")
	lbls_at = nrow(y1) - as.numeric(rownames(lbl_set))
	
	# daily downloads
	par(mar=c(3,5,3,3))
	plot(y3$num_downloads, type='l', main=n, xlab=NULL, xaxt='n', ylab="downloads / day", col='cornsilk2', ylim=c(0, max_d))
	axis(1, at=lbls_at, labels=lbls)
	abline(v=nrow(y1) - as.numeric(rownames(subset(y1, stamp$yday == 0))))
	
	lines(runavg(y3$num_downloads), lwd=2, col='cornflowerblue')
	lines(y2$num_downloads, col='cornsilk3')
	lines(runavg(y2$num_downloads), lwd=3, col='blue')
	lines(y1$num_downloads, col='cornsilk4')
	lines(runavg(y1$num_downloads), lwd=4, col='blue4')
	
	# number of updates (scaled)
	max_upd = max(d$num_updates, na.rm=T)
	factor = max_upd / max_d
	lines(d[(365+runavg_n):1,]$num_updates / factor, lty='dotted')
	axis(4, at=c(0, max_d), labels=c(0, max_upd))
	
	# legend
	legend('topleft',
		c(max(y1$stamp$year + 1900, na.rm=T), max(y2$stamp$year + 1900, na.rm=T), max(y3$stamp$year + 1900, na.rm=T), "Updates"),
		lwd=c(4,3,2,1), lty=c('solid', 'solid', 'solid', 'dotted'), col=c('blue4', 'blue', 'cornflowerblue', 'black'))
	
	if (to_file) {
		dev.off()
	}
}
