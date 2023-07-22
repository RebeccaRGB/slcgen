#!/usr/bin/env python

from __future__ import print_function
import fontforge
import math
import psMat
import sys


class SLCParameters:
	def __init__(
		self,
		ascent=None, descent=None, width=None,
		pixelHeight=None, pixelWidth=None,
		diagonalFillAngle=None,
		diagonalFillWeight=None,
		diagonalSpaceWeight=None,
		boxLightWeight=None, boxHeavyWeight=None, boxDoubleGap=None,
		boxArcRadius=None, boxTickLength=None, boxLineTruncate=None,
		separationTop=None, separationRight=None,
		separationBottom=None, separationLeft=None,
		file=None
	):
		# Calculate values for font metrics.
		self.ascent = ascent if ascent is not None else descent * 4 if descent is not None else 800
		self.descent = descent if descent is not None else ascent / 4 if ascent is not None else 200
		self.height = self.ascent + self.descent
		self.width = width if width is not None else self.height
		# Calculate values for shade characters.
		self.pixelHeight = pixelHeight if pixelHeight is not None else pixelWidth if pixelWidth is not None else 20
		self.pixelWidth = pixelWidth if pixelWidth is not None else pixelHeight if pixelHeight is not None else 20
		# Calculate values for diagonal fill characters.
		self.diagonalFillAngle = diagonalFillAngle if diagonalFillAngle is not None else math.degrees(math.atan2(self.height, self.width))
		if diagonalFillWeight is None and diagonalSpaceWeight is None:
			s = abs(math.sin(math.radians(self.diagonalFillAngle)))
			c = abs(math.cos(math.radians(self.diagonalFillAngle)))
			self.diagonalFillWeight = (self.height * c + self.width * s) / 16
			self.diagonalSpaceWeight = self.diagonalFillWeight
		else:
			self.diagonalFillWeight = diagonalFillWeight if diagonalFillWeight is not None else diagonalSpaceWeight
			self.diagonalSpaceWeight = diagonalSpaceWeight if diagonalSpaceWeight is not None else diagonalFillWeight
		# Calculate values for box drawing characters.
		if boxLightWeight is None and boxHeavyWeight is None:
			self.boxLightWeight = self.height / 9
			self.boxHeavyWeight = self.boxLightWeight * 2
		else:
			self.boxLightWeight = boxLightWeight if boxLightWeight is not None else boxHeavyWeight / 2
			self.boxHeavyWeight = boxHeavyWeight if boxHeavyWeight is not None else boxLightWeight * 2
		self.boxDoubleGap = boxDoubleGap if boxDoubleGap is not None else self.boxLightWeight
		self.boxArcRadius = boxArcRadius if boxArcRadius is not None else min(self.height, self.width) / 2
		self.boxTickLength = boxTickLength if boxTickLength is not None else min(max(self.height, self.width) / 3, min(self.height, self.width) / 2)
		self.boxLineTruncate = boxLineTruncate if boxLineTruncate is not None else True
		# Calculate values for separated block mosaic characters.
		self.separationTop = (
			separationTop if separationTop is not None else
			separationBottom if separationBottom is not None else
			separationRight if separationRight is not None and separationLeft is None else
			separationLeft if separationLeft is not None and separationRight is None else
			self.height / 18
		)
		self.separationRight = (
			separationRight if separationRight is not None else
			separationLeft if separationLeft is not None else
			separationTop if separationTop is not None and separationBottom is None else
			separationBottom if separationBottom is not None and separationTop is None else
			self.height / 18
		)
		self.separationBottom = (
			separationBottom if separationBottom is not None else
			separationTop if separationTop is not None else
			separationRight if separationRight is not None and separationLeft is None else
			separationLeft if separationLeft is not None and separationRight is None else
			self.height / 18
		)
		self.separationLeft = (
			separationLeft if separationLeft is not None else
			separationRight if separationRight is not None else
			separationTop if separationTop is not None and separationBottom is None else
			separationBottom if separationBottom is not None and separationTop is None else
			self.height / 18
		)
		# Set output file.
		self.file = file if file is not None else 'out.sfd'


class GlyphProxy:
	def __init__(self, params, glyph):
		self.params = params
		self.glyph = glyph

	def rawrect(self, x1, y1, x2, y2):
		pen = self.glyph.glyphPen(replace=False)
		pen.moveTo((round(x1), round(y1)))
		pen.lineTo((round(x2), round(y1)))
		pen.lineTo((round(x2), round(y2)))
		pen.lineTo((round(x1), round(y2)))
		pen.closePath()
		self.glyph.simplify()
		return self

	def rect(self, x1, y1, x2, y2):
		return self.rawrect(
			self.params.width * x1,
			self.params.ascent - self.params.height * y1,
			self.params.width * x2,
			self.params.ascent - self.params.height * y2
		)

	def _rawrectccw(self, x1, y1, x2, y2):
		pen = self.glyph.glyphPen(replace=False)
		pen.moveTo((round(x1), round(y1)))
		pen.lineTo((round(x1), round(y2)))
		pen.lineTo((round(x2), round(y2)))
		pen.lineTo((round(x2), round(y1)))
		pen.closePath()
		self.glyph.simplify()
		return self

	def _rectccw(self, x1, y1, x2, y2):
		return self._rawrectccw(
			self.params.width * x1,
			self.params.ascent - self.params.height * y1,
			self.params.width * x2,
			self.params.ascent - self.params.height * y2
		)

	def rawpoly(self, *points):
		pen = self.glyph.glyphPen(replace=False)
		pen.moveTo((round(points[0][0]), round(points[0][1])))
		for p in points[1:]:
			pen.lineTo((round(p[0]), round(p[1])))
		pen.closePath()
		self.glyph.simplify()
		return self

	def poly(self, *points):
		return self.rawpoly(*[
			(self.params.width * x, self.params.ascent - self.params.height * y)
			for x, y in points
		])

	def _stripcontrolpoints(self):
		polygons = []
		for li in range(len(self.glyph.layers)):
			for ci in range(len(self.glyph.layers[li])):
				contour = self.glyph.layers[li][ci]
				points = [(p.x, p.y) for p in contour if p.on_curve]
				polygons.append(points)
		self.glyph.clear()
		self.glyph.width = self.params.width
		for polygon in polygons:
			self.rawpoly(*polygon)

	def shade(self, rows, cols, inverse):
		for y in range(rows):
			for x in range(cols):
				# Make sure this condition is preserved exactly when porting this code.
				if ((x + y) & 1) ^ ((rows + cols) & 1) ^ (0 if inverse else 1):
					self.rect(float(x)/cols, float(y)/rows, float(x+1)/cols, float(y+1)/rows)
		return self

	def shadepart(self, rows, cols, inverse, points, union):
		for y in range(rows):
			for x in range(cols):
				# Make sure this condition is preserved exactly when porting this code.
				if ((x + y) & 1) ^ ((rows + cols) & 1) ^ (0 if inverse else 1):
					self.rect(float(x)/cols, float(y)/rows, float(x+1)/cols, float(y+1)/rows)
		self.poly(*points)
		if union:
			self.glyph.removeOverlap()
		else:
			self.glyph.intersect()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def ltshade(self, rows, cols):
		for y in range(rows // 2):
			for x in range(cols):
				if ((x + y) & 1) == ((rows + cols) & 1):
					self.rect(float(x)/cols, float(y*2)/rows, float(x+1)/cols, float(y*2+1)/rows)
		return self

	def dkshade(self, rows, cols):
		for y in range(rows // 2):
			for x in range(cols):
				if ((x + y) & 1) == ((rows + cols) & 1):
					self._rectccw(float(x)/cols, float(y*2)/rows, float(x+1)/cols, float(y*2+1)/rows)
		self.rect(0, 0, 1, 1)
		self.glyph.removeOverlap()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def diagfill(self, angle):
		x = self.params.height + self.params.width
		self.rawrect(-x, +self.params.diagonalFillWeight*0.5, +x, -self.params.diagonalFillWeight*0.5)
		for y in range(round(x / (self.params.diagonalFillWeight + self.params.diagonalSpaceWeight))):
			y1 = (y+1.5) * self.params.diagonalFillWeight + (y+1) * self.params.diagonalSpaceWeight
			y2 = (y+0.5) * self.params.diagonalFillWeight + (y+1) * self.params.diagonalSpaceWeight
			self.rawrect(-x, +y1, +x, +y2)
			self.rawrect(-x, -y2, +x, -y1)
		self.glyph.transform(psMat.rotate(math.radians(angle)))
		self.glyph.transform(psMat.translate(self.params.width*0.5, self.params.ascent-self.params.height*0.5))
		self.rect(0, 0, 1, 1)
		self.glyph.intersect()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def bitmap(self, rows, cols, n):
		for y in range(rows):
			for x in range(cols):
				if n & 1:
					self.rect(float(x)/cols, float(y)/rows, float(x+1)/cols, float(y+1)/rows)
				n >>= 1
		self.glyph.removeOverlap()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def sepmap(self, rows, cols, n):
		for y in range(rows):
			for x in range(cols):
				if n & 1:
					self.rawrect(
						self.params.width * x / float(cols) + self.params.separationLeft,
						self.params.ascent - self.params.height * y / float(rows) - self.params.separationTop,
						self.params.width * (x+1) / float(cols) - self.params.separationRight,
						self.params.ascent - self.params.height * (y+1) / float(rows) + self.params.separationBottom
					)
				n >>= 1
		return self

	def _extendpoints(self, points):
		x0, y0 = points[0]
		x1, y1 = points[1]
		x2, y2 = points[-2]
		x3, y3 = points[-1]
		return [(x0-(x1-x0),y0-(y1-y0))] + points[1:-1] + [(x3-(x2-x3),y3-(y2-y3))]

	def _boxdrawline(self, line, weight, truncate):
		# We use SPACE!? as a temporary glyph buffer because FONTFORGE IS DUMB
		# and has NO WAY to STROKE ONLY SPECIFIC CONTOURS and NO WAY to REMOVE
		# ENCODING SLOTS from Python. WHAT THE F--- IS WRONG WITH YOU FONTFORGE
		tmpglyph = self.glyph.font.createChar(32)
		tmppen = tmpglyph.glyphPen(replace=True)
		if truncate:
			line = self._extendpoints(line)
			tmppen.moveTo((round(self.params.width * line[0][0]), round(self.params.ascent - self.params.height * line[0][1])))
			for p in line[1:]:
				tmppen.lineTo((round(self.params.width * p[0]), round(self.params.ascent - self.params.height * p[1])))
			tmppen.endPath()
			tmpglyph.stroke('circular', weight, 'square', 'miter')
			tmppen.moveTo((0, self.params.ascent))
			tmppen.lineTo((self.params.width, self.params.ascent))
			tmppen.lineTo((self.params.width, -self.params.descent))
			tmppen.lineTo((0, -self.params.descent))
			tmppen.closePath()
			tmpglyph.intersect()
		else:
			tmppen.moveTo((round(self.params.width * line[0][0]), round(self.params.ascent - self.params.height * line[0][1])))
			for p in line[1:]:
				tmppen.lineTo((round(self.params.width * p[0]), round(self.params.ascent - self.params.height * p[1])))
			tmppen.endPath()
			tmpglyph.stroke('circular', weight, 'butt', 'miter')
		tmpglyph.simplify()
		tmpglyph.draw(self.glyph.glyphPen(replace=False))
		tmpglyph.clear()
		tmpglyph.width = self.params.width
		return self

	def boxdrawlight(self, *lines):
		for line in lines:
			self._boxdrawline(line, self.params.boxLightWeight, False)
		self.glyph.removeOverlap()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def boxdrawheavy(self, *lines):
		for line in lines:
			self._boxdrawline(line, self.params.boxHeavyWeight, False)
		self.glyph.removeOverlap()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def boxdrawmixed(self, lightLines, heavyLines):
		for line in lightLines:
			self._boxdrawline(line, self.params.boxLightWeight, False)
		for line in heavyLines:
			self._boxdrawline(line, self.params.boxHeavyWeight, False)
		self.glyph.removeOverlap()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def boxdrawdiag(self, *lines):
		for line in lines:
			self._boxdrawline(line, self.params.boxLightWeight, self.params.boxLineTruncate)
		self.glyph.removeOverlap()
		self.glyph.simplify()
		self._stripcontrolpoints()
		return self

	def rawellipse(self, cx, cy, orx, ory, irx, iry, bx1, by1, bx2, by2):
		pen = self.glyph.glyphPen(replace=False)
		if orx > 0 and ory > 0:
			oc = fontforge.unitShape(0)
			oc.transform(psMat.scale(orx, ory))
			oc.transform(psMat.translate(cx, cy))
			oc.draw(pen)
		if irx > 0 and iry > 0:
			ic = fontforge.unitShape(0)
			ic.transform(psMat.scale(irx, iry))
			ic.transform(psMat.translate(cx, cy))
			ic.reverseDirection()
			ic.draw(pen)
		self.rawrect(bx1, by1, bx2, by2)
		self.glyph.intersect()
		self.glyph.simplify()
		self.glyph.round()
		return self

	def ellipse(self, cx, cy, orx, ory, irx, iry, bx1, by1, bx2, by2):
		return self.rawellipse(
			self.params.width * cx,
			self.params.ascent - self.params.height * cy,
			self.params.width * orx,
			self.params.height * ory,
			self.params.width * irx,
			self.params.height * iry,
			self.params.width * bx1,
			self.params.ascent - self.params.height * by1,
			self.params.width * bx2,
			self.params.ascent - self.params.height * by2
		)

	def boxdrawarc(self, dx, dy):
		self.rawellipse(
			self.params.width / 2.0 + self.params.boxArcRadius * dx,
			self.params.ascent - self.params.height / 2.0 - self.params.boxArcRadius * dy,
			self.params.boxArcRadius + self.params.boxLightWeight / 2.0,
			self.params.boxArcRadius + self.params.boxLightWeight / 2.0,
			self.params.boxArcRadius - self.params.boxLightWeight / 2.0,
			self.params.boxArcRadius - self.params.boxLightWeight / 2.0,
			self.params.width / 2.0 - self.params.boxArcRadius,
			self.params.ascent - self.params.height / 2.0 + self.params.boxArcRadius,
			self.params.width / 2.0 + self.params.boxArcRadius,
			self.params.ascent - self.params.height / 2.0 - self.params.boxArcRadius
		)
		if dx < 0 and (self.params.width / 2.0 - self.params.boxArcRadius) > 0:
			self.rawrect(
				0,
				self.params.ascent - self.params.height / 2.0 + self.params.boxLightWeight / 2.0,
				self.params.width / 2.0 - self.params.boxArcRadius,
				self.params.ascent - self.params.height / 2.0 - self.params.boxLightWeight / 2.0
			)
		if dx > 0 and (self.params.width / 2.0 + self.params.boxArcRadius) < self.params.width:
			self.rawrect(
				self.params.width / 2.0 + self.params.boxArcRadius,
				self.params.ascent - self.params.height / 2.0 + self.params.boxLightWeight / 2.0,
				self.params.width,
				self.params.ascent - self.params.height / 2.0 - self.params.boxLightWeight / 2.0
			)
		if dy < 0 and (self.params.ascent - self.params.height / 2.0 + self.params.boxArcRadius) < self.params.ascent:
			self.rawrect(
				self.params.width / 2.0 - self.params.boxLightWeight / 2.0,
				self.params.ascent,
				self.params.width / 2.0 + self.params.boxLightWeight / 2.0,
				self.params.ascent - self.params.height / 2.0 + self.params.boxArcRadius
			)
		if dy > 0 and (self.params.ascent - self.params.height / 2.0 - self.params.boxArcRadius) > -self.params.descent:
			self.rawrect(
				self.params.width / 2.0 - self.params.boxLightWeight / 2.0,
				self.params.ascent - self.params.height / 2.0 - self.params.boxArcRadius,
				self.params.width / 2.0 + self.params.boxLightWeight / 2.0,
				-self.params.descent
			)
		self.glyph.removeOverlap()
		self.glyph.simplify()
		self.glyph.round()
		return self


class FontProxy:
	def __init__(self, params, font):
		self.params = params
		self.font = font

	def mkfont(self):
		self.font.os2_winascent_add = self.font.os2_windescent_add = 0
		self.font.os2_typoascent_add = self.font.os2_typodescent_add = 0
		self.font.hhea_ascent_add = self.font.hhea_descent_add = 0
		self.font.ascent = self.font.os2_winascent = self.params.ascent
		self.font.os2_typoascent = self.font.hhea_ascent = self.params.ascent
		self.font.descent = self.font.os2_windescent = self.params.descent
		self.font.os2_typodescent = self.font.hhea_descent = -self.params.descent
		self.font.os2_typolinegap = self.font.hhea_linegap = 0
		self.font.encoding = 'UnicodeFull'
		return self

	def mkglyph(self, name, cp):
		glyph = self.font.createChar(cp)
		glyph.clear()
		glyph.width = self.params.width
		return GlyphProxy(self.params, glyph)

	def output(self):
		self.font.save(self.params.file)


def slcgen(**kwargs):
	# Calculate parameters.
	p = SLCParameters(**kwargs)
	xe = p.boxLightWeight / (p.width * 2.0)
	ye = p.boxLightWeight / (p.height * 2.0)
	xg = (p.boxLightWeight + p.boxDoubleGap) / (p.width * 2.0)
	yg = (p.boxLightWeight + p.boxDoubleGap) / (p.height * 2.0)
	xgd = (p.boxLightWeight + p.boxDoubleGap) / (math.sin(math.atan2(p.height, p.width)) * p.width * 2)
	ygd = (p.boxLightWeight + p.boxDoubleGap) / (math.cos(math.atan2(p.height, p.width)) * p.height * 2)
	ty = p.boxTickLength / p.height
	tx = p.boxTickLength / p.width
	# Create SFD.
	f = FontProxy(p, fontforge.font())
	f.mkfont()
	# Create glyphs in Miscellaneous Technical block.
	f.mkglyph('space',   0x0020)
	f.mkglyph('uni00A0', 0x00A0)
	f.mkglyph('uni23B8', 0x23B8).boxdrawlight([(xe,0), (xe,1)])
	f.mkglyph('uni23B9', 0x23B9).boxdrawlight([(1-xe,0), (1-xe,1)])
	f.mkglyph('uni23BA', 0x23BA).boxdrawlight([(0,ye), (1,ye)])
	f.mkglyph('uni23BB', 0x23BB).boxdrawlight([(0,0.25+ye*0.5), (1,0.25+ye*0.5)])
	f.mkglyph('uni23BC', 0x23BC).boxdrawlight([(0,0.75-ye*0.5), (1,0.75-ye*0.5)])
	f.mkglyph('uni23BD', 0x23BD).boxdrawlight([(0,1-ye), (1,1-ye)])
	# Create glyphs in Box Drawing block.
	f.mkglyph('SF100000',0x2500).boxdrawlight([(0,0.5),(1,0.5)])
	f.mkglyph('uni2501', 0x2501).boxdrawheavy([(0,0.5),(1,0.5)])
	f.mkglyph('SF110000',0x2502).boxdrawlight([(0.5,0),(0.5,1)])
	f.mkglyph('uni2503', 0x2503).boxdrawheavy([(0.5,0),(0.5,1)])
	f.mkglyph('uni2504', 0x2504).boxdrawlight([(0+xe,0.5),(1./3-xe,0.5)], [(1./3+xe,0.5),(2./3-xe,0.5)], [(2./3+xe,0.5),(1-xe,0.5)])
	f.mkglyph('uni2505', 0x2505).boxdrawheavy([(0+xe,0.5),(1./3-xe,0.5)], [(1./3+xe,0.5),(2./3-xe,0.5)], [(2./3+xe,0.5),(1-xe,0.5)])
	f.mkglyph('uni2506', 0x2506).boxdrawlight([(0.5,0+ye),(0.5,1./3-ye)], [(0.5,1./3+ye),(0.5,2./3-ye)], [(0.5,2./3+ye),(0.5,1-ye)])
	f.mkglyph('uni2507', 0x2507).boxdrawheavy([(0.5,0+ye),(0.5,1./3-ye)], [(0.5,1./3+ye),(0.5,2./3-ye)], [(0.5,2./3+ye),(0.5,1-ye)])
	f.mkglyph('uni2508', 0x2508).boxdrawlight([(0+xe,0.5),(0.25-xe,0.5)], [(0.25+xe,0.5),(0.5-xe,0.5)], [(0.5+xe,0.5),(0.75-xe,0.5)], [(0.75+xe,0.5),(1-xe,0.5)])
	f.mkglyph('uni2509', 0x2509).boxdrawheavy([(0+xe,0.5),(0.25-xe,0.5)], [(0.25+xe,0.5),(0.5-xe,0.5)], [(0.5+xe,0.5),(0.75-xe,0.5)], [(0.75+xe,0.5),(1-xe,0.5)])
	f.mkglyph('uni250A', 0x250A).boxdrawlight([(0.5,0+ye),(0.5,0.25-ye)], [(0.5,0.25+ye),(0.5,0.5-ye)], [(0.5,0.5+ye),(0.5,0.75-ye)], [(0.5,0.75+ye),(0.5,1-ye)])
	f.mkglyph('uni250B', 0x250B).boxdrawheavy([(0.5,0+ye),(0.5,0.25-ye)], [(0.5,0.25+ye),(0.5,0.5-ye)], [(0.5,0.5+ye),(0.5,0.75-ye)], [(0.5,0.75+ye),(0.5,1-ye)])
	f.mkglyph('SF010000',0x250C).boxdrawlight([(0.5,1),(0.5,0.5),(1,0.5)])
	f.mkglyph('uni250D', 0x250D).boxdrawmixed([[(0.5,1),(0.5,0.5)]], [[(0.5-xe,0.5),(1,0.5)]])
	f.mkglyph('uni250E', 0x250E).boxdrawmixed([[(0.5,0.5),(1,0.5)]], [[(0.5,1),(0.5,0.5-ye)]])
	f.mkglyph('uni250F', 0x250F).boxdrawheavy([(0.5,1),(0.5,0.5),(1,0.5)])
	f.mkglyph('SF030000',0x2510).boxdrawlight([(0.5,1),(0.5,0.5),(0,0.5)])
	f.mkglyph('uni2511', 0x2511).boxdrawmixed([[(0.5,1),(0.5,0.5)]], [[(0.5+xe,0.5),(0,0.5)]])
	f.mkglyph('uni2512', 0x2512).boxdrawmixed([[(0.5,0.5),(0,0.5)]], [[(0.5,1),(0.5,0.5-ye)]])
	f.mkglyph('uni2513', 0x2513).boxdrawheavy([(0.5,1),(0.5,0.5),(0,0.5)])
	f.mkglyph('SF020000',0x2514).boxdrawlight([(0.5,0),(0.5,0.5),(1,0.5)])
	f.mkglyph('uni2515', 0x2515).boxdrawmixed([[(0.5,0),(0.5,0.5)]], [[(0.5-xe,0.5),(1,0.5)]])
	f.mkglyph('uni2516', 0x2516).boxdrawmixed([[(0.5,0.5),(1,0.5)]], [[(0.5,0),(0.5,0.5+ye)]])
	f.mkglyph('uni2517', 0x2517).boxdrawheavy([(0.5,0),(0.5,0.5),(1,0.5)])
	f.mkglyph('SF040000',0x2518).boxdrawlight([(0.5,0),(0.5,0.5),(0,0.5)])
	f.mkglyph('uni2519', 0x2519).boxdrawmixed([[(0.5,0),(0.5,0.5)]], [[(0.5+xe,0.5),(0,0.5)]])
	f.mkglyph('uni251A', 0x251A).boxdrawmixed([[(0.5,0.5),(0,0.5)]], [[(0.5,0),(0.5,0.5+ye)]])
	f.mkglyph('uni251B', 0x251B).boxdrawheavy([(0.5,0),(0.5,0.5),(0,0.5)])
	f.mkglyph('SF080000',0x251C).boxdrawlight([(0.5,0),(0.5,1)],[(0.5,0.5),(1,0.5)])
	f.mkglyph('uni251D', 0x251D).boxdrawmixed([[(0.5,0),(0.5,1)]], [[(0.5,0.5),(1,0.5)]])
	f.mkglyph('uni251E', 0x251E).boxdrawmixed([[(0.5,1),(0.5,0.5),(1,0.5)]], [[(0.5,0),(0.5,0.5+ye)]])
	f.mkglyph('uni251F', 0x251F).boxdrawmixed([[(0.5,0),(0.5,0.5),(1,0.5)]], [[(0.5,1),(0.5,0.5-ye)]])
	f.mkglyph('uni2520', 0x2520).boxdrawmixed([[(0.5,0.5),(1,0.5)]], [[(0.5,0),(0.5,1)]])
	f.mkglyph('uni2521', 0x2521).boxdrawmixed([[(0.5,0.5),(0.5,1)]], [[(0.5,0),(0.5,0.5),(1,0.5)]])
	f.mkglyph('uni2522', 0x2522).boxdrawmixed([[(0.5,0.5),(0.5,0)]], [[(0.5,1),(0.5,0.5),(1,0.5)]])
	f.mkglyph('uni2523', 0x2523).boxdrawheavy([(0.5,0),(0.5,1)], [(0.5,0.5),(1,0.5)])
	f.mkglyph('SF090000',0x2524).boxdrawlight([(0.5,0),(0.5,1)],[(0.5,0.5),(0,0.5)])
	f.mkglyph('uni2525', 0x2525).boxdrawmixed([[(0.5,0),(0.5,1)]], [[(0.5,0.5),(0,0.5)]])
	f.mkglyph('uni2526', 0x2526).boxdrawmixed([[(0.5,1),(0.5,0.5),(0,0.5)]], [[(0.5,0),(0.5,0.5+ye)]])
	f.mkglyph('uni2527', 0x2527).boxdrawmixed([[(0.5,0),(0.5,0.5),(0,0.5)]], [[(0.5,1),(0.5,0.5-ye)]])
	f.mkglyph('uni2528', 0x2528).boxdrawmixed([[(0.5,0.5),(0,0.5)]], [[(0.5,0),(0.5,1)]])
	f.mkglyph('uni2529', 0x2529).boxdrawmixed([[(0.5,0.5),(0.5,1)]], [[(0.5,0),(0.5,0.5),(0,0.5)]])
	f.mkglyph('uni252A', 0x252A).boxdrawmixed([[(0.5,0.5),(0.5,0)]], [[(0.5,1),(0.5,0.5),(0,0.5)]])
	f.mkglyph('uni252B', 0x252B).boxdrawheavy([(0.5,0),(0.5,1)], [(0.5,0.5),(0,0.5)])
	f.mkglyph('SF060000',0x252C).boxdrawlight([(0,0.5),(1,0.5)], [(0.5,0.5),(0.5,1)])
	f.mkglyph('uni252D', 0x252D).boxdrawmixed([[(0.5,1),(0.5,0.5),(1,0.5)]], [[(0,0.5),(0.5+xe,0.5)]])
	f.mkglyph('uni252E', 0x252E).boxdrawmixed([[(0.5,1),(0.5,0.5),(0,0.5)]], [[(1,0.5),(0.5-xe,0.5)]])
	f.mkglyph('uni252F', 0x252F).boxdrawmixed([[(0.5,0.5),(0.5,1)]], [[(0,0.5),(1,0.5)]])
	f.mkglyph('uni2530', 0x2530).boxdrawmixed([[(0,0.5),(1,0.5)]], [[(0.5,0.5),(0.5,1)]])
	f.mkglyph('uni2531', 0x2531).boxdrawmixed([[(0.5,0.5),(1,0.5)]], [[(0.5,1),(0.5,0.5),(0,0.5)]])
	f.mkglyph('uni2532', 0x2532).boxdrawmixed([[(0.5,0.5),(0,0.5)]], [[(0.5,1),(0.5,0.5),(1,0.5)]])
	f.mkglyph('uni2533', 0x2533).boxdrawheavy([(0,0.5),(1,0.5)], [(0.5,0.5),(0.5,1)])
	f.mkglyph('SF070000',0x2534).boxdrawlight([(0,0.5),(1,0.5)], [(0.5,0.5),(0.5,0)])
	f.mkglyph('uni2535', 0x2535).boxdrawmixed([[(0.5,0),(0.5,0.5),(1,0.5)]], [[(0,0.5),(0.5+xe,0.5)]])
	f.mkglyph('uni2536', 0x2536).boxdrawmixed([[(0.5,0),(0.5,0.5),(0,0.5)]], [[(1,0.5),(0.5-xe,0.5)]])
	f.mkglyph('uni2537', 0x2537).boxdrawmixed([[(0.5,0.5),(0.5,0)]], [[(0,0.5),(1,0.5)]])
	f.mkglyph('uni2538', 0x2538).boxdrawmixed([[(0,0.5),(1,0.5)]], [[(0.5,0.5),(0.5,0)]])
	f.mkglyph('uni2539', 0x2539).boxdrawmixed([[(0.5,0.5),(1,0.5)]], [[(0.5,0),(0.5,0.5),(0,0.5)]])
	f.mkglyph('uni253A', 0x253A).boxdrawmixed([[(0.5,0.5),(0,0.5)]], [[(0.5,0),(0.5,0.5),(1,0.5)]])
	f.mkglyph('uni253B', 0x253B).boxdrawheavy([(0,0.5),(1,0.5)], [(0.5,0.5),(0.5,0)])
	f.mkglyph('SF050000',0x253C).boxdrawlight([(0,0.5),(1,0.5)], [(0.5,0),(0.5,1)])
	f.mkglyph('uni253D', 0x253D).boxdrawmixed([[(0.5,0),(0.5,1)], [(0.5,0.5),(1,0.5)]], [[(0,0.5),(0.5,0.5)]])
	f.mkglyph('uni253E', 0x253E).boxdrawmixed([[(0.5,0),(0.5,1)], [(0.5,0.5),(0,0.5)]], [[(1,0.5),(0.5,0.5)]])
	f.mkglyph('uni253F', 0x253F).boxdrawmixed([[(0.5,0),(0.5,1)]], [[(0,0.5),(1,0.5)]])
	f.mkglyph('uni2540', 0x2540).boxdrawmixed([[(0,0.5),(1,0.5)], [(0.5,0.5),(0.5,1)]], [[(0.5,0),(0.5,0.5)]])
	f.mkglyph('uni2541', 0x2541).boxdrawmixed([[(0,0.5),(1,0.5)], [(0.5,0.5),(0.5,0)]], [[(0.5,1),(0.5,0.5)]])
	f.mkglyph('uni2542', 0x2542).boxdrawmixed([[(0,0.5),(1,0.5)]], [[(0.5,0),(0.5,1)]])
	f.mkglyph('uni2543', 0x2543).boxdrawmixed([[(0.5,1),(0.5,0.5),(1,0.5)]], [[(0.5,0),(0.5,0.5),(0,0.5)]])
	f.mkglyph('uni2544', 0x2544).boxdrawmixed([[(0.5,1),(0.5,0.5),(0,0.5)]], [[(0.5,0),(0.5,0.5),(1,0.5)]])
	f.mkglyph('uni2545', 0x2545).boxdrawmixed([[(0.5,0),(0.5,0.5),(1,0.5)]], [[(0.5,1),(0.5,0.5),(0,0.5)]])
	f.mkglyph('uni2546', 0x2546).boxdrawmixed([[(0.5,0),(0.5,0.5),(0,0.5)]], [[(0.5,1),(0.5,0.5),(1,0.5)]])
	f.mkglyph('uni2547', 0x2547).boxdrawmixed([[(0.5,0.5),(0.5,1)]], [[(0,0.5),(1,0.5)], [(0.5,0),(0.5,0.5)]])
	f.mkglyph('uni2548', 0x2548).boxdrawmixed([[(0.5,0.5),(0.5,0)]], [[(0,0.5),(1,0.5)], [(0.5,1),(0.5,0.5)]])
	f.mkglyph('uni2549', 0x2549).boxdrawmixed([[(0.5,0.5),(1,0.5)]], [[(0.5,0),(0.5,1)], [(0,0.5),(0.5,0.5)]])
	f.mkglyph('uni254A', 0x254A).boxdrawmixed([[(0.5,0.5),(0,0.5)]], [[(0.5,0),(0.5,1)], [(1,0.5),(0.5,0.5)]])
	f.mkglyph('uni254B', 0x254B).boxdrawheavy([(0,0.5),(1,0.5)], [(0.5,0),(0.5,1)])
	f.mkglyph('uni254C', 0x254C).boxdrawlight([(0+xe,0.5),(0.5-xe,0.5)], [(0.5+xe,0.5),(1-xe,0.5)])
	f.mkglyph('uni254D', 0x254D).boxdrawheavy([(0+xe,0.5),(0.5-xe,0.5)], [(0.5+xe,0.5),(1-xe,0.5)])
	f.mkglyph('uni254E', 0x254E).boxdrawlight([(0.5,0+ye),(0.5,0.5-ye)], [(0.5,0.5+ye),(0.5,1-ye)])
	f.mkglyph('uni254F', 0x254F).boxdrawheavy([(0.5,0+ye),(0.5,0.5-ye)], [(0.5,0.5+ye),(0.5,1-ye)])
	f.mkglyph('SF430000',0x2550).boxdrawlight([(0,0.5-yg),(1,0.5-yg)], [(0,0.5+yg),(1,0.5+yg)])
	f.mkglyph('SF240000',0x2551).boxdrawlight([(0.5-xg,0),(0.5-xg,1)], [(0.5+xg,0),(0.5+xg,1)])
	f.mkglyph('SF510000',0x2552).boxdrawlight([(0.5,1),(0.5,0.5-yg),(1,0.5-yg)], [(0.5,0.5+yg),(1,0.5+yg)])
	f.mkglyph('SF520000',0x2553).boxdrawlight([(1,0.5),(0.5-xg,0.5),(0.5-xg,1)], [(0.5+xg,0.5),(0.5+xg,1)])
	f.mkglyph('SF390000',0x2554).boxdrawlight([(0.5-xg,1),(0.5-xg,0.5-yg),(1,0.5-yg)], [(0.5+xg,1),(0.5+xg,0.5+yg),(1,0.5+yg)])
	f.mkglyph('SF220000',0x2555).boxdrawlight([(0.5,1),(0.5,0.5-yg),(0,0.5-yg)], [(0.5,0.5+yg),(0,0.5+yg)])
	f.mkglyph('SF210000',0x2556).boxdrawlight([(0,0.5),(0.5+xg,0.5),(0.5+xg,1)], [(0.5-xg,0.5),(0.5-xg,1)])
	f.mkglyph('SF250000',0x2557).boxdrawlight([(0.5+xg,1),(0.5+xg,0.5-yg),(0,0.5-yg)], [(0.5-xg,1),(0.5-xg,0.5+yg),(0,0.5+yg)])
	f.mkglyph('SF500000',0x2558).boxdrawlight([(0.5,0),(0.5,0.5+yg),(1,0.5+yg)], [(0.5,0.5-yg),(1,0.5-yg)])
	f.mkglyph('SF490000',0x2559).boxdrawlight([(1,0.5),(0.5-xg,0.5),(0.5-xg,0)], [(0.5+xg,0.5),(0.5+xg,0)])
	f.mkglyph('SF380000',0x255A).boxdrawlight([(0.5-xg,0),(0.5-xg,0.5+yg),(1,0.5+yg)], [(0.5+xg,0),(0.5+xg,0.5-yg),(1,0.5-yg)])
	f.mkglyph('SF280000',0x255B).boxdrawlight([(0.5,0),(0.5,0.5+yg),(0,0.5+yg)], [(0.5,0.5-yg),(0,0.5-yg)])
	f.mkglyph('SF270000',0x255C).boxdrawlight([(0,0.5),(0.5+xg,0.5),(0.5+xg,0)], [(0.5-xg,0.5),(0.5-xg,0)])
	f.mkglyph('SF260000',0x255D).boxdrawlight([(0.5+xg,0),(0.5+xg,0.5+yg),(0,0.5+yg)], [(0.5-xg,0),(0.5-xg,0.5-yg),(0,0.5-yg)])
	f.mkglyph('SF360000',0x255E).boxdrawlight([(0.5,0),(0.5,1)], [(0.5,0.5-yg),(1,0.5-yg)], [(0.5,0.5+yg),(1,0.5+yg)])
	f.mkglyph('SF370000',0x255F).boxdrawlight([(0.5-xg,0),(0.5-xg,1)], [(0.5+xg,0),(0.5+xg,1)], [(0.5+xg,0.5),(1,0.5)])
	f.mkglyph('SF420000',0x2560).boxdrawlight([(0.5-xg,0),(0.5-xg,1)], [(0.5+xg,0),(0.5+xg,0.5-yg),(1,0.5-yg)], [(0.5+xg,1),(0.5+xg,0.5+yg),(1,0.5+yg)])
	f.mkglyph('SF190000',0x2561).boxdrawlight([(0.5,0),(0.5,1)], [(0.5,0.5-yg),(0,0.5-yg)], [(0.5,0.5+yg),(0,0.5+yg)])
	f.mkglyph('SF200000',0x2562).boxdrawlight([(0.5+xg,0),(0.5+xg,1)], [(0.5-xg,0),(0.5-xg,1)], [(0.5-xg,0.5),(0,0.5)])
	f.mkglyph('SF230000',0x2563).boxdrawlight([(0.5+xg,0),(0.5+xg,1)], [(0.5-xg,0),(0.5-xg,0.5-yg),(0,0.5-yg)], [(0.5-xg,1),(0.5-xg,0.5+yg),(0,0.5+yg)])
	f.mkglyph('SF470000',0x2564).boxdrawlight([(0,0.5-yg),(1,0.5-yg)], [(0,0.5+yg),(1,0.5+yg)], [(0.5,0.5+yg),(0.5,1)])
	f.mkglyph('SF480000',0x2565).boxdrawlight([(0,0.5),(1,0.5)], [(0.5-xg,0.5),(0.5-xg,1)], [(0.5+xg,0.5),(0.5+xg,1)])
	f.mkglyph('SF410000',0x2566).boxdrawlight([(0,0.5-yg),(1,0.5-yg)], [(0,0.5+yg),(0.5-xg,0.5+yg),(0.5-xg,1)], [(1,0.5+yg),(0.5+xg,0.5+yg),(0.5+xg,1)])
	f.mkglyph('SF450000',0x2567).boxdrawlight([(0,0.5+yg),(1,0.5+yg)], [(0,0.5-yg),(1,0.5-yg)], [(0.5,0.5-yg),(0.5,0)])
	f.mkglyph('SF460000',0x2568).boxdrawlight([(0,0.5),(1,0.5)], [(0.5-xg,0.5),(0.5-xg,0)], [(0.5+xg,0.5),(0.5+xg,0)])
	f.mkglyph('SF400000',0x2569).boxdrawlight([(0,0.5+yg),(1,0.5+yg)], [(0,0.5-yg),(0.5-xg,0.5-yg),(0.5-xg,0)], [(1,0.5-yg),(0.5+xg,0.5-yg),(0.5+xg,0)])
	f.mkglyph('SF540000',0x256A).boxdrawlight([(0,0.5-yg),(1,0.5-yg)], [(0,0.5+yg),(1,0.5+yg)], [(0.5,0),(0.5,1)])
	f.mkglyph('SF530000',0x256B).boxdrawlight([(0.5-xg,0),(0.5-xg,1)], [(0.5+xg,0),(0.5+xg,1)], [(0,0.5),(1,0.5)])
	f.mkglyph('SF440000',0x256C).boxdrawlight([(0.5-xg,0),(0.5-xg,0.5-yg),(0,0.5-yg)], [(0.5+xg,0),(0.5+xg,0.5-yg),(1,0.5-yg)], [(0.5-xg,1),(0.5-xg,0.5+yg),(0,0.5+yg)], [(0.5+xg,1),(0.5+xg,0.5+yg),(1,0.5+yg)])
	f.mkglyph('uni256D', 0x256D).boxdrawarc(+1, +1)
	f.mkglyph('uni256E', 0x256E).boxdrawarc(-1, +1)
	f.mkglyph('uni256F', 0x256F).boxdrawarc(-1, -1)
	f.mkglyph('uni2570', 0x2570).boxdrawarc(+1, -1)
	f.mkglyph('uni2571', 0x2571).boxdrawdiag([(1,0),(0,1)])
	f.mkglyph('uni2572', 0x2572).boxdrawdiag([(0,0),(1,1)])
	f.mkglyph('uni2573', 0x2573).boxdrawdiag([(1,0),(0,1)], [(0,0),(1,1)])
	f.mkglyph('uni2574', 0x2574).boxdrawlight([(0,0.5),(0.5,0.5)])
	f.mkglyph('uni2575', 0x2575).boxdrawlight([(0.5,0),(0.5,0.5)])
	f.mkglyph('uni2576', 0x2576).boxdrawlight([(1,0.5),(0.5,0.5)])
	f.mkglyph('uni2577', 0x2577).boxdrawlight([(0.5,1),(0.5,0.5)])
	f.mkglyph('uni2578', 0x2578).boxdrawheavy([(0,0.5),(0.5,0.5)])
	f.mkglyph('uni2579', 0x2579).boxdrawheavy([(0.5,0),(0.5,0.5)])
	f.mkglyph('uni257A', 0x257A).boxdrawheavy([(1,0.5),(0.5,0.5)])
	f.mkglyph('uni257B', 0x257B).boxdrawheavy([(0.5,1),(0.5,0.5)])
	f.mkglyph('uni257C', 0x257C).boxdrawmixed([[(0,0.5),(0.5,0.5)]], [[(1,0.5),(0.5,0.5)]])
	f.mkglyph('uni257D', 0x257D).boxdrawmixed([[(0.5,0),(0.5,0.5)]], [[(0.5,1),(0.5,0.5)]])
	f.mkglyph('uni257E', 0x257E).boxdrawmixed([[(1,0.5),(0.5,0.5)]], [[(0,0.5),(0.5,0.5)]])
	f.mkglyph('uni257F', 0x257F).boxdrawmixed([[(0.5,1),(0.5,0.5)]], [[(0.5,0),(0.5,0.5)]])
	# Create glyphs in Block Elements block.
	f.mkglyph('upblock', 0x2580).rect(0, 0, 1, 0.5)
	f.mkglyph('uni2581', 0x2581).rect(0, 0.875, 1, 1)
	f.mkglyph('uni2582', 0x2582).rect(0, 0.75, 1, 1)
	f.mkglyph('uni2583', 0x2583).rect(0, 0.625, 1, 1)
	f.mkglyph('dnblock', 0x2584).rect(0, 0.5, 1, 1)
	f.mkglyph('uni2585', 0x2585).rect(0, 0.375, 1, 1)
	f.mkglyph('uni2586', 0x2586).rect(0, 0.25, 1, 1)
	f.mkglyph('uni2587', 0x2587).rect(0, 0.125, 1, 1)
	f.mkglyph('block',   0x2588).rect(0, 0, 1, 1)
	f.mkglyph('uni2589', 0x2589).rect(0, 0, 0.875, 1)
	f.mkglyph('uni258A', 0x258A).rect(0, 0, 0.75, 1)
	f.mkglyph('uni258B', 0x258B).rect(0, 0, 0.625, 1)
	f.mkglyph('lfblock', 0x258C).rect(0, 0, 0.5, 1)
	f.mkglyph('uni258D', 0x258D).rect(0, 0, 0.375, 1)
	f.mkglyph('uni258E', 0x258E).rect(0, 0, 0.25, 1)
	f.mkglyph('uni258F', 0x258F).rect(0, 0, 0.125, 1)
	f.mkglyph('rtblock', 0x2590).rect(0.5, 0, 1, 1)
	f.mkglyph('ltshade', 0x2591).ltshade(p.pixelHeight, p.pixelWidth)
	f.mkglyph('shade',   0x2592).shade(p.pixelHeight, p.pixelWidth, False)
	f.mkglyph('dkshade', 0x2593).dkshade(p.pixelHeight, p.pixelWidth)
	f.mkglyph('uni2594', 0x2594).rect(0, 0, 1, 0.125)
	f.mkglyph('uni2595', 0x2595).rect(0.875, 0, 1, 1)
	f.mkglyph('uni2596', 0x2596).rect(0, 0.5, 0.5, 1)
	f.mkglyph('uni2597', 0x2597).rect(0.5, 0.5, 1, 1)
	f.mkglyph('uni2598', 0x2598).rect(0, 0, 0.5, 0.5)
	f.mkglyph('uni2599', 0x2599).poly((0,0), (0.5,0), (0.5,0.5), (1,0.5), (1,1), (0,1))
	f.mkglyph('uni259A', 0x259A).rect(0, 0, 0.5, 0.5).rect(0.5, 0.5, 1, 1)
	f.mkglyph('uni259B', 0x259B).poly((0,0), (1,0), (1,0.5), (0.5,0.5), (0.5,1), (0,1))
	f.mkglyph('uni259C', 0x259C).poly((0,0), (1,0), (1,1), (0.5,1), (0.5,0.5), (0,0.5))
	f.mkglyph('uni259D', 0x259D).rect(0.5, 0, 1, 0.5)
	f.mkglyph('uni259E', 0x259E).rect(0.5, 0, 1, 0.5).rect(0, 0.5, 0.5, 1)
	f.mkglyph('uni259F', 0x259F).poly((0.5,0), (1,0), (1,1), (0,1), (0,0.5), (0.5,0.5))
	# Create glyphs in Geometric Shapes block.
	f.mkglyph('uni25E2', 0x25E2).poly((0,1), (1,0), (1,1))
	f.mkglyph('uni25E3', 0x25E3).poly((0,0), (1,1), (0,1))
	f.mkglyph('uni25E4', 0x25E4).poly((0,0), (1,0), (0,1))
	f.mkglyph('uni25E5', 0x25E5).poly((0,0), (1,0), (1,1))
	f.mkglyph('uni27CA', 0x27CA).boxdrawmixed([[(0.5,0),(0.5,1)]], [[(0.25,0.5),(0.75,0.5)]])
	# Create glyphs in Symbols for Legacy Computing block.
	f.mkglyph('u1FB00', 0x1FB00).rect(0, 0, 0.5, 1./3)
	f.mkglyph('u1FB01', 0x1FB01).rect(0.5, 0, 1, 1./3)
	f.mkglyph('u1FB02', 0x1FB02).rect(0, 0, 1, 1./3)
	f.mkglyph('u1FB03', 0x1FB03).rect(0, 1./3, 0.5, 2./3)
	f.mkglyph('u1FB04', 0x1FB04).rect(0, 0, 0.5, 2./3)
	f.mkglyph('u1FB05', 0x1FB05).rect(0.5, 0, 1, 1./3).rect(0, 1./3, 0.5, 2./3)
	f.mkglyph('u1FB06', 0x1FB06).poly((0,0), (1,0), (1,1./3), (0.5,1./3), (0.5,2./3), (0,2./3))
	f.mkglyph('u1FB07', 0x1FB07).rect(0.5, 1./3, 1, 2./3)
	f.mkglyph('u1FB08', 0x1FB08).rect(0, 0, 0.5, 1./3).rect(0.5, 1./3, 1, 2./3)
	f.mkglyph('u1FB09', 0x1FB09).rect(0.5, 0, 1, 2./3)
	f.mkglyph('u1FB0A', 0x1FB0A).poly((0,0), (1,0), (1,2./3), (0.5,2./3), (0.5,1./3), (0,1./3))
	f.mkglyph('u1FB0B', 0x1FB0B).rect(0, 1./3, 1, 2./3)
	f.mkglyph('u1FB0C', 0x1FB0C).poly((0,0), (0.5,0), (0.5,1./3), (1,1./3), (1,2./3), (0,2./3))
	f.mkglyph('u1FB0D', 0x1FB0D).poly((0.5,0), (1,0), (1,2./3), (0,2./3), (0,1./3), (0.5,1./3))
	f.mkglyph('u1FB0E', 0x1FB0E).rect(0, 0, 1, 2./3)
	f.mkglyph('u1FB0F', 0x1FB0F).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB10', 0x1FB10).rect(0, 0, 0.5, 1./3).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB11', 0x1FB11).rect(0.5, 0, 1, 1./3).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB12', 0x1FB12).rect(0, 0, 1, 1./3).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB13', 0x1FB13).rect(0, 1./3, 0.5, 1)
	f.mkglyph('u1FB14', 0x1FB14).rect(0.5, 0, 1, 1./3).rect(0, 1./3, 0.5, 1)
	f.mkglyph('u1FB15', 0x1FB15).poly((0,0), (1,0), (1,1./3), (0.5,1./3), (0.5,1), (0,1))
	f.mkglyph('u1FB16', 0x1FB16).rect(0.5, 1./3, 1, 2./3).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB17', 0x1FB17).rect(0, 0, 0.5, 1./3).rect(0.5, 1./3, 1, 2./3).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB18', 0x1FB18).rect(0.5, 0, 1, 2./3).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB19', 0x1FB19).poly((0,0), (1,0), (1,2./3), (0.5,2./3), (0.5,1./3), (0,1./3)).rect(0, 2./3, 0.5, 1)
	f.mkglyph('u1FB1A', 0x1FB1A).poly((0,1./3), (1,1./3), (1,2./3), (0.5,2./3), (0.5,1), (0,1))
	f.mkglyph('u1FB1B', 0x1FB1B).poly((0,0), (0.5,0), (0.5,1./3), (1,1./3), (1,2./3), (0.5,2./3), (0.5,1), (0,1))
	f.mkglyph('u1FB1C', 0x1FB1C).poly((0.5,0), (1,0), (1,2./3), (0.5,2./3), (0.5,1), (0,1), (0,1./3), (0.5,1./3))
	f.mkglyph('u1FB1D', 0x1FB1D).poly((0,0), (1,0), (1,2./3), (0.5,2./3), (0.5,1), (0,1))
	f.mkglyph('u1FB1E', 0x1FB1E).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB1F', 0x1FB1F).rect(0, 0, 0.5, 1./3).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB20', 0x1FB20).rect(0.5, 0, 1, 1./3).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB21', 0x1FB21).rect(0, 0, 1, 1./3).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB22', 0x1FB22).rect(0, 1./3, 0.5, 2./3).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB23', 0x1FB23).rect(0, 0, 0.5, 2./3).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB24', 0x1FB24).rect(0.5, 0, 1, 1./3).rect(0, 1./3, 0.5, 2./3).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB25', 0x1FB25).poly((0,0), (1,0), (1,1./3), (0.5,1./3), (0.5,2./3), (0,2./3)).rect(0.5, 2./3, 1, 1)
	f.mkglyph('u1FB26', 0x1FB26).rect(0.5, 1./3, 1, 1)
	f.mkglyph('u1FB27', 0x1FB27).rect(0, 0, 0.5, 1./3).rect(0.5, 1./3, 1, 1)
	f.mkglyph('u1FB28', 0x1FB28).poly((0,0), (1,0), (1,1), (0.5,1), (0.5,1./3), (0,1./3))
	f.mkglyph('u1FB29', 0x1FB29).poly((0,1./3), (1,1./3), (1,1), (0.5,1), (0.5,2./3), (0,2./3))
	f.mkglyph('u1FB2A', 0x1FB2A).poly((0,0), (0.5,0), (0.5,1./3), (1,1./3), (1,1), (0.5,1), (0.5,2./3), (0,2./3))
	f.mkglyph('u1FB2B', 0x1FB2B).poly((0.5,0), (1,0), (1,1), (0.5,1), (0.5,2./3), (0,2./3), (0,1./3), (0.5,1./3))
	f.mkglyph('u1FB2C', 0x1FB2C).poly((0,0), (1,0), (1,1), (0.5,1), (0.5,2./3), (0,2./3))
	f.mkglyph('u1FB2D', 0x1FB2D).rect(0, 2./3, 1, 1)
	f.mkglyph('u1FB2E', 0x1FB2E).rect(0, 0, 0.5, 1./3).rect(0, 2./3, 1, 1)
	f.mkglyph('u1FB2F', 0x1FB2F).rect(0.5, 0, 1, 1./3).rect(0, 2./3, 1, 1)
	f.mkglyph('u1FB30', 0x1FB30).rect(0, 0, 1, 1./3).rect(0, 2./3, 1, 1)
	f.mkglyph('u1FB31', 0x1FB31).poly((0,1./3), (0.5,1./3), (0.5,2./3), (1,2./3), (1,1), (0,1))
	f.mkglyph('u1FB32', 0x1FB32).poly((0,0), (0.5,0), (0.5,2./3), (1,2./3), (1,1), (0,1))
	f.mkglyph('u1FB33', 0x1FB33).rect(0.5, 0, 1, 1./3).poly((0,1./3), (0.5,1./3), (0.5,2./3), (1,2./3), (1,1), (0,1))
	f.mkglyph('u1FB34', 0x1FB34).poly((0,0), (1,0), (1,1./3), (0.5,1./3), (0.5,2./3), (1,2./3), (1,1), (0,1))
	f.mkglyph('u1FB35', 0x1FB35).poly((0.5,1./3), (1,1./3), (1,1), (0,1), (0,2./3), (0.5,2./3))
	f.mkglyph('u1FB36', 0x1FB36).rect(0, 0, 0.5, 1./3).poly((0.5,1./3), (1,1./3), (1,1), (0,1), (0,2./3), (0.5,2./3))
	f.mkglyph('u1FB37', 0x1FB37).poly((0.5,0), (1,0), (1,1), (0,1), (0,2./3), (0.5,2./3))
	f.mkglyph('u1FB38', 0x1FB38).poly((0,0), (1,0), (1,1), (0,1), (0,2./3), (0.5,2./3), (0.5,1./3), (0,1./3))
	f.mkglyph('u1FB39', 0x1FB39).rect(0, 1./3, 1, 1)
	f.mkglyph('u1FB3A', 0x1FB3A).poly((0,0), (0.5,0), (0.5,1./3), (1,1./3), (1,1), (0,1))
	f.mkglyph('u1FB3B', 0x1FB3B).poly((0.5,0), (1,0), (1,1), (0,1), (0,1./3), (0.5,1./3))
	f.mkglyph('u1FB3C', 0x1FB3C).poly((0,2./3), (0.5,1), (0,1))
	f.mkglyph('u1FB3D', 0x1FB3D).poly((0,2./3), (1,1), (0,1))
	f.mkglyph('u1FB3E', 0x1FB3E).poly((0,1./3), (0.5,1), (0,1))
	f.mkglyph('u1FB3F', 0x1FB3F).poly((0,1./3), (1,1), (0,1))
	f.mkglyph('u1FB40', 0x1FB40).poly((0,0), (0.5,1), (0,1))
	f.mkglyph('u1FB41', 0x1FB41).poly((0,1./3), (0.5,0), (1,0), (1,1), (0,1))
	f.mkglyph('u1FB42', 0x1FB42).poly((0,1./3), (1,0), (1,1), (0,1))
	f.mkglyph('u1FB43', 0x1FB43).poly((0,2./3), (0.5,0), (1,0), (1,1), (0,1))
	f.mkglyph('u1FB44', 0x1FB44).poly((0,2./3), (1,0), (1,1), (0,1))
	f.mkglyph('u1FB45', 0x1FB45).poly((0,1), (0.5,0), (1,0), (1,1))
	f.mkglyph('u1FB46', 0x1FB46).poly((0,2./3), (1,1./3), (1,1), (0,1))
	f.mkglyph('u1FB47', 0x1FB47).poly((0.5,1), (1,2./3), (1,1))
	f.mkglyph('u1FB48', 0x1FB48).poly((0,1), (1,2./3), (1,1))
	f.mkglyph('u1FB49', 0x1FB49).poly((0.5,1), (1,1./3), (1,1))
	f.mkglyph('u1FB4A', 0x1FB4A).poly((0,1), (1,1./3), (1,1))
	f.mkglyph('u1FB4B', 0x1FB4B).poly((0.5,1), (1,0), (1,1))
	f.mkglyph('u1FB4C', 0x1FB4C).poly((0,0), (0.5,0), (1,1./3), (1,1), (0,1))
	f.mkglyph('u1FB4D', 0x1FB4D).poly((0,0), (1,1./3), (1,1), (0,1))
	f.mkglyph('u1FB4E', 0x1FB4E).poly((0,0), (0.5,0), (1,2./3), (1,1), (0,1))
	f.mkglyph('u1FB4F', 0x1FB4F).poly((0,0), (1,2./3), (1,1), (0,1))
	f.mkglyph('u1FB50', 0x1FB50).poly((0,0), (0.5,0), (1,1), (0,1))
	f.mkglyph('u1FB51', 0x1FB51).poly((0,1./3), (1,2./3), (1,1), (0,1))
	f.mkglyph('u1FB52', 0x1FB52).poly((0,0), (1,0), (1,1), (0.5,1), (0,2./3))
	f.mkglyph('u1FB53', 0x1FB53).poly((0,0), (1,0), (1,1), (0,2./3))
	f.mkglyph('u1FB54', 0x1FB54).poly((0,0), (1,0), (1,1), (0.5,1), (0,1./3))
	f.mkglyph('u1FB55', 0x1FB55).poly((0,0), (1,0), (1,1), (0,1./3))
	f.mkglyph('u1FB56', 0x1FB56).poly((0,0), (1,0), (1,1), (0.5,1))
	f.mkglyph('u1FB57', 0x1FB57).poly((0,0), (0.5,0), (0,1./3))
	f.mkglyph('u1FB58', 0x1FB58).poly((0,0), (1,0), (0,1./3))
	f.mkglyph('u1FB59', 0x1FB59).poly((0,0), (0.5,0), (0,2./3))
	f.mkglyph('u1FB5A', 0x1FB5A).poly((0,0), (1,0), (0,2./3))
	f.mkglyph('u1FB5B', 0x1FB5B).poly((0,0), (0.5,0), (0,1))
	f.mkglyph('u1FB5C', 0x1FB5C).poly((0,0), (1,0), (1,1./3), (0,2./3))
	f.mkglyph('u1FB5D', 0x1FB5D).poly((0,0), (1,0), (1,2./3), (0.5,1), (0,1))
	f.mkglyph('u1FB5E', 0x1FB5E).poly((0,0), (1,0), (1,2./3), (0,1))
	f.mkglyph('u1FB5F', 0x1FB5F).poly((0,0), (1,0), (1,1./3), (0.5,1), (0,1))
	f.mkglyph('u1FB60', 0x1FB60).poly((0,0), (1,0), (1,1./3), (0,1))
	f.mkglyph('u1FB61', 0x1FB61).poly((0,0), (1,0), (0.5,1), (0,1))
	f.mkglyph('u1FB62', 0x1FB62).poly((0.5,0), (1,0), (1,1./3))
	f.mkglyph('u1FB63', 0x1FB63).poly((0,0), (1,0), (1,1./3))
	f.mkglyph('u1FB64', 0x1FB64).poly((0.5,0), (1,0), (1,2./3))
	f.mkglyph('u1FB65', 0x1FB65).poly((0,0), (1,0), (1,2./3))
	f.mkglyph('u1FB66', 0x1FB66).poly((0.5,0), (1,0), (1,1))
	f.mkglyph('u1FB67', 0x1FB67).poly((0,0), (1,0), (1,2./3), (0,1./3))
	f.mkglyph('u1FB68', 0x1FB68).poly((0,0), (1,0), (1,1), (0,1), (0.5,0.5))
	f.mkglyph('u1FB69', 0x1FB69).poly((1,0), (1,1), (0,1), (0,0), (0.5,0.5))
	f.mkglyph('u1FB6A', 0x1FB6A).poly((1,1), (0,1), (0,0), (1,0), (0.5,0.5))
	f.mkglyph('u1FB6B', 0x1FB6B).poly((0,1), (0,0), (1,0), (1,1), (0.5,0.5))
	f.mkglyph('u1FB6C', 0x1FB6C).poly((0,1), (0,0), (0.5,0.5))
	f.mkglyph('u1FB6D', 0x1FB6D).poly((0,0), (1,0), (0.5,0.5))
	f.mkglyph('u1FB6E', 0x1FB6E).poly((1,0), (1,1), (0.5,0.5))
	f.mkglyph('u1FB6F', 0x1FB6F).poly((1,1), (0,1), (0.5,0.5))
	f.mkglyph('u1FB70', 0x1FB70).rect(0.125, 0, 0.25, 1)
	f.mkglyph('u1FB71', 0x1FB71).rect(0.25, 0, 0.375, 1)
	f.mkglyph('u1FB72', 0x1FB72).rect(0.375, 0, 0.5, 1)
	f.mkglyph('u1FB73', 0x1FB73).rect(0.5, 0, 0.625, 1)
	f.mkglyph('u1FB74', 0x1FB74).rect(0.625, 0, 0.75, 1)
	f.mkglyph('u1FB75', 0x1FB75).rect(0.75, 0, 0.875, 1)
	f.mkglyph('u1FB76', 0x1FB76).rect(0, 0.125, 1, 0.25)
	f.mkglyph('u1FB77', 0x1FB77).rect(0, 0.25, 1, 0.375)
	f.mkglyph('u1FB78', 0x1FB78).rect(0, 0.375, 1, 0.5)
	f.mkglyph('u1FB79', 0x1FB79).rect(0, 0.5, 1, 0.625)
	f.mkglyph('u1FB7A', 0x1FB7A).rect(0, 0.625, 1, 0.75)
	f.mkglyph('u1FB7B', 0x1FB7B).rect(0, 0.75, 1, 0.875)
	f.mkglyph('u1FB7C', 0x1FB7C).poly((0,0), (0.125,0), (0.125,0.875), (1,0.875), (1,1), (0,1))
	f.mkglyph('u1FB7D', 0x1FB7D).poly((0,0), (1,0), (1,0.125), (0.125,0.125), (0.125,1), (0,1))
	f.mkglyph('u1FB7E', 0x1FB7E).poly((0,0), (1,0), (1,1), (0.875,1), (0.875,0.125), (0,0.125))
	f.mkglyph('u1FB7F', 0x1FB7F).poly((0.875,0), (1,0), (1,1), (0,1), (0,0.875), (0.875,0.875))
	f.mkglyph('u1FB80', 0x1FB80).rect(0, 0, 1, 0.125).rect(0, 0.875, 1, 1)
	f.mkglyph('u1FB81', 0x1FB81).rect(0, 0, 1, 0.125).rect(0, 0.25, 1, 0.375).rect(0, 0.5, 1, 0.625).rect(0, 0.875, 1, 1)
	f.mkglyph('u1FB82', 0x1FB82).rect(0, 0, 1, 0.25)
	f.mkglyph('u1FB83', 0x1FB83).rect(0, 0, 1, 0.375)
	f.mkglyph('u1FB84', 0x1FB84).rect(0, 0, 1, 0.625)
	f.mkglyph('u1FB85', 0x1FB85).rect(0, 0, 1, 0.75)
	f.mkglyph('u1FB86', 0x1FB86).rect(0, 0, 1, 0.875)
	f.mkglyph('u1FB87', 0x1FB87).rect(0.75, 0, 1, 1)
	f.mkglyph('u1FB88', 0x1FB88).rect(0.625, 0, 1, 1)
	f.mkglyph('u1FB89', 0x1FB89).rect(0.375, 0, 1, 1)
	f.mkglyph('u1FB8A', 0x1FB8A).rect(0.25, 0, 1, 1)
	f.mkglyph('u1FB8B', 0x1FB8B).rect(0.125, 0, 1, 1)
	f.mkglyph('u1FB8C', 0x1FB8C).shadepart(p.pixelHeight, p.pixelWidth, False, [(0,0), (0.5,0), (0.5,1), (0,1)], False)
	f.mkglyph('u1FB8D', 0x1FB8D).shadepart(p.pixelHeight, p.pixelWidth, False, [(0.5,0), (1,0), (1,1), (0.5,1)], False)
	f.mkglyph('u1FB8E', 0x1FB8E).shadepart(p.pixelHeight, p.pixelWidth, False, [(0,0), (1,0), (1,0.5), (0,0.5)], False)
	f.mkglyph('u1FB8F', 0x1FB8F).shadepart(p.pixelHeight, p.pixelWidth, False, [(0,0.5), (1,0.5), (1,1), (0,1)], False)
	f.mkglyph('u1FB90', 0x1FB90).shade(p.pixelHeight, p.pixelWidth, True)
	f.mkglyph('u1FB91', 0x1FB91).shadepart(p.pixelHeight, p.pixelWidth, True, [(0,0), (1,0), (1,0.5), (0,0.5)], True)
	f.mkglyph('u1FB92', 0x1FB92).shadepart(p.pixelHeight, p.pixelWidth, True, [(0,0.5), (1,0.5), (1,1), (0,1)], True)
	f.mkglyph('u1FB93', 0x1FB93).shadepart(p.pixelHeight, p.pixelWidth, True, [(0,0), (0.5,0), (0.5,1), (0,1)], True)
	f.mkglyph('u1FB94', 0x1FB94).shadepart(p.pixelHeight, p.pixelWidth, True, [(0.5,0), (1,0), (1,1), (0.5,1)], True)
	f.mkglyph('u1FB95', 0x1FB95).shade(4, 4, False)
	f.mkglyph('u1FB96', 0x1FB96).shade(4, 4, True)
	f.mkglyph('u1FB97', 0x1FB97).rect(0, 0.25, 1, 0.5).rect(0, 0.75, 1, 1)
	f.mkglyph('u1FB98', 0x1FB98).diagfill(-p.diagonalFillAngle)
	f.mkglyph('u1FB99', 0x1FB99).diagfill(+p.diagonalFillAngle)
	f.mkglyph('u1FB9A', 0x1FB9A).poly((0,0), (1,0), (0.5,0.5)).poly((1,1), (0,1), (0.5,0.5))
	f.mkglyph('u1FB9B', 0x1FB9B).poly((0,1), (0,0), (0.5,0.5)).poly((1,0), (1,1), (0.5,0.5))
	f.mkglyph('u1FB9C', 0x1FB9C).shadepart(p.pixelHeight, p.pixelWidth, False, [(0,0), (1,0), (0,1)], False)
	f.mkglyph('u1FB9D', 0x1FB9D).shadepart(p.pixelHeight, p.pixelWidth, False, [(0,0), (1,0), (1,1)], False)
	f.mkglyph('u1FB9E', 0x1FB9E).shadepart(p.pixelHeight, p.pixelWidth, False, [(0,1), (1,0), (1,1)], False)
	f.mkglyph('u1FB9F', 0x1FB9F).shadepart(p.pixelHeight, p.pixelWidth, False, [(0,0), (1,1), (0,1)], False)
	f.mkglyph('u1FBA0', 0x1FBA0).boxdrawdiag([(0,0.5),(0.5,0)])
	f.mkglyph('u1FBA1', 0x1FBA1).boxdrawdiag([(0.5,0),(1,0.5)])
	f.mkglyph('u1FBA2', 0x1FBA2).boxdrawdiag([(0,0.5),(0.5,1)])
	f.mkglyph('u1FBA3', 0x1FBA3).boxdrawdiag([(0.5,1),(1,0.5)])
	f.mkglyph('u1FBA4', 0x1FBA4).boxdrawdiag([(0.5,0),(0,0.5),(0.5,1)])
	f.mkglyph('u1FBA5', 0x1FBA5).boxdrawdiag([(0.5,0),(1,0.5),(0.5,1)])
	f.mkglyph('u1FBA6', 0x1FBA6).boxdrawdiag([(0,0.5),(0.5,1),(1,0.5)])
	f.mkglyph('u1FBA7', 0x1FBA7).boxdrawdiag([(0,0.5),(0.5,0),(1,0.5)])
	f.mkglyph('u1FBA8', 0x1FBA8).boxdrawdiag([(0,0.5),(0.5,0)], [(0.5,1),(1,0.5)])
	f.mkglyph('u1FBA9', 0x1FBA9).boxdrawdiag([(0.5,0),(1,0.5)], [(0,0.5),(0.5,1)])
	f.mkglyph('u1FBAA', 0x1FBAA).boxdrawdiag([(0.5,0),(1,0.5),(0.5,1),(0,0.5)])
	f.mkglyph('u1FBAB', 0x1FBAB).boxdrawdiag([(0.5,0),(0,0.5),(0.5,1),(1,0.5)])
	f.mkglyph('u1FBAC', 0x1FBAC).boxdrawdiag([(0,0.5),(0.5,0),(1,0.5),(0.5,1)])
	f.mkglyph('u1FBAD', 0x1FBAD).boxdrawdiag([(1,0.5),(0.5,0),(0,0.5),(0.5,1)])
	f.mkglyph('u1FBAE', 0x1FBAE).boxdrawdiag([(0.5,0),(1,0.5),(0.5,1),(0,0.5),(0.5,0)])
	f.mkglyph('u1FBAF', 0x1FBAF).boxdrawmixed([[(0,0.5),(1,0.5)]], [[(0.5,0.25),(0.5,0.75)]])
	f.mkglyph('u1FBCE', 0x1FBCE).rect(0, 0, 2./3, 1)
	f.mkglyph('u1FBCF', 0x1FBCF).rect(0, 0, 1./3, 1)
	f.mkglyph('u1FBD0', 0x1FBD0).boxdrawdiag([(0,1),(1,0.5)])
	f.mkglyph('u1FBD1', 0x1FBD1).boxdrawdiag([(0,0.5),(1,0)])
	f.mkglyph('u1FBD2', 0x1FBD2).boxdrawdiag([(0,0),(1,0.5)])
	f.mkglyph('u1FBD3', 0x1FBD3).boxdrawdiag([(0,0.5),(1,1)])
	f.mkglyph('u1FBD4', 0x1FBD4).boxdrawdiag([(0,0),(0.5,1)])
	f.mkglyph('u1FBD5', 0x1FBD5).boxdrawdiag([(0.5,0),(1,1)])
	f.mkglyph('u1FBD6', 0x1FBD6).boxdrawdiag([(1,0),(0.5,1)])
	f.mkglyph('u1FBD7', 0x1FBD7).boxdrawdiag([(0.5,0),(0,1)])
	f.mkglyph('u1FBD8', 0x1FBD8).boxdrawdiag([(0,0),(0.5,0.5),(1,0)])
	f.mkglyph('u1FBD9', 0x1FBD9).boxdrawdiag([(1,0),(0.5,0.5),(1,1)])
	f.mkglyph('u1FBDA', 0x1FBDA).boxdrawdiag([(0,1),(0.5,0.5),(1,1)])
	f.mkglyph('u1FBDB', 0x1FBDB).boxdrawdiag([(0,0),(0.5,0.5),(0,1)])
	f.mkglyph('u1FBDC', 0x1FBDC).boxdrawdiag([(0,0),(0.5,1),(1,0)])
	f.mkglyph('u1FBDD', 0x1FBDD).boxdrawdiag([(1,0),(0,0.5),(1,1)])
	f.mkglyph('u1FBDE', 0x1FBDE).boxdrawdiag([(0,1),(0.5,0),(1,1)])
	f.mkglyph('u1FBDF', 0x1FBDF).boxdrawdiag([(0,0),(1,0.5),(0,1)])
	f.mkglyph('u1FBE0', 0x1FBE0).ellipse(0.5, 0, 0.5, 0.5, 0.5-xe*2, 0.5-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1FBE1', 0x1FBE1).ellipse(1, 0.5, 0.5, 0.5, 0.5-xe*2, 0.5-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1FBE2', 0x1FBE2).ellipse(0.5, 1, 0.5, 0.5, 0.5-xe*2, 0.5-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1FBE3', 0x1FBE3).ellipse(0, 0.5, 0.5, 0.5, 0.5-xe*2, 0.5-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1FBE4', 0x1FBE4).rect(0.25, 0, 0.75, 0.5)
	f.mkglyph('u1FBE5', 0x1FBE5).rect(0.25, 0.5, 0.75, 1)
	f.mkglyph('u1FBE6', 0x1FBE6).rect(0, 0.25, 0.5, 0.75)
	f.mkglyph('u1FBE7', 0x1FBE7).rect(0.5, 0.25, 1, 0.75)
	f.mkglyph('u1FBE8', 0x1FBE8).ellipse(0.5, 0, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	f.mkglyph('u1FBE9', 0x1FBE9).ellipse(1, 0.5, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	f.mkglyph('u1FBEA', 0x1FBEA).ellipse(0.5, 1, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	f.mkglyph('u1FBEB', 0x1FBEB).ellipse(0, 0.5, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	f.mkglyph('u1FBEC', 0x1FBEC).ellipse(1, 0, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	f.mkglyph('u1FBED', 0x1FBED).ellipse(0, 1, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	f.mkglyph('u1FBEE', 0x1FBEE).ellipse(1, 1, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	f.mkglyph('u1FBEF', 0x1FBEF).ellipse(0, 0, 0.5, 0.5, 0, 0, 0, 0, 1, 1)
	# Create glyphs in Symbols for Legacy Computing Supplement block, Sharp MZ section.
	f.mkglyph('u1CC1B', 0x1CC1B).boxdrawlight([(0,0.5),(1-xe,0.5),(1-xe,0)])
	f.mkglyph('u1CC1C', 0x1CC1C).boxdrawlight([(0,0.5),(1-xe,0.5),(1-xe,1)])
	f.mkglyph('u1CC1D', 0x1CC1D).boxdrawlight([(xe,0.5+ye),(xe,ye),(1,ye)])
	f.mkglyph('u1CC1E', 0x1CC1E).boxdrawlight([(xe,0.5-ye),(xe,1-ye),(1,1-ye)])
	f.mkglyph('u1CC1F', 0x1CC1F).boxdrawdiag([(1-xgd,0),(0,1-ygd)], [(1,ygd),(xgd,1)])
	f.mkglyph('u1CC20', 0x1CC20).boxdrawdiag([(0,ygd),(1-xgd,1)], [(xgd,0),(1,1-ygd)])
	for i in range(1, 16):
		f.mkglyph('u%X' % (0x1CC20 + i), 0x1CC20 + i).sepmap(2, 2, i)
	f.mkglyph('u1CC30', 0x1CC30).ellipse(2, 2, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC31', 0x1CC31).ellipse(1, 2, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC32', 0x1CC32).ellipse(0, 2, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC33', 0x1CC33).ellipse(-1, 2, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC34', 0x1CC34).ellipse(2, 1, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC35', 0x1CC35).ellipse(1, 1, 1, 1, 1-xe*2, 1-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC36', 0x1CC36).ellipse(0, 1, 1, 1, 1-xe*2, 1-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC37', 0x1CC37).ellipse(-1, 1, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC38', 0x1CC38).ellipse(2, 0, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC39', 0x1CC39).ellipse(1, 0, 1, 1, 1-xe*2, 1-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC3A', 0x1CC3A).ellipse(0, 0, 1, 1, 1-xe*2, 1-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC3B', 0x1CC3B).ellipse(-1, 0, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC3C', 0x1CC3C).ellipse(2, -1, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC3D', 0x1CC3D).ellipse(1, -1, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC3E', 0x1CC3E).ellipse(0, -1, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	f.mkglyph('u1CC3F', 0x1CC3F).ellipse(-1, -1, 2, 2, 2-xe*2, 2-ye*2, 0, 0, 1, 1)
	# Create glyphs in Symbols for Legacy Computing Supplement block, Kaypro/Aquarius section.
	for i, n in enumerate(x for x in range(0x100) if x not in [
		0x00,0x01,0x02,0x03,0x05,0x0A,0x0F,0x14,0x28,0x3F,0x40,0x50,0x55,
		0x5A,0x5F,0x80,0xA0,0xA5,0xAA,0xAF,0xC0,0xF0,0xF5,0xFA,0xFC,0xFF
	]):
		f.mkglyph('u%X' % (0x1CD00 + i), 0x1CD00 + i).bitmap(4, 2, n)
	f.mkglyph('u1CDF4', 0x1CDF4).rect(0.25, 0, 0.75, 1)
	# Create glyphs in Symbols for Legacy Computing Supplement block, OSI/HP/Teletext/Robotron section.
	f.mkglyph('u1CE0D', 0x1CE0D).boxdrawlight([(0,0.5),(1./3,0.5)], [(2./3,0.5),(1,0.5)])
	f.mkglyph('u1CE0E', 0x1CE0E).boxdrawlight([(1./3,0.5),(2./3,0.5)])
	f.mkglyph('u1CE0F', 0x1CE0F).boxdrawlight([(0,0.5),(1-xe,0.5),(1-xe,0.5+ty)])
	f.mkglyph('u1CE10', 0x1CE10).boxdrawlight([(0,0.5),(1,0.5)], [(2./3-xe,0.5),(2./3-xe,0.5+ty)])
	f.mkglyph('u1CE11', 0x1CE11).boxdrawlight([(0,0.5),(1-xe,0.5),(1-xe,0.5+ty)], [(1./3-xe,0.5),(1./3-xe,0.5+ty)])
	f.mkglyph('u1CE12', 0x1CE12).boxdrawlight([(0,0.5),(1-xe,0.5),(1-xe,0.5+ty)], [(2./3-xe,0.5),(2./3-xe,0.5+ty)], [(1./3-xe,0.5),(1./3-xe,0.5+ty)])
	f.mkglyph('u1CE13', 0x1CE13).boxdrawlight([(0.5,0),(0.5,1)], [(0.5-tx,1./3+ye),(0.5,1./3+ye)])
	f.mkglyph('u1CE14', 0x1CE14).boxdrawlight([(0.5-tx,ye),(0.5,ye),(0.5,1)], [(0.5-tx,2./3+ye),(0.5,2./3+ye)])
	f.mkglyph('u1CE15', 0x1CE15).boxdrawlight([(0.5-tx,ye),(0.5,ye),(0.5,1)], [(0.5-tx,1./3+ye),(0.5,1./3+ye)], [(0.5-tx,2./3+ye),(0.5,2./3+ye)])
	f.mkglyph('u1CE16', 0x1CE16).boxdrawlight([(0.5,1),(0.5,ye),(1,ye)])
	f.mkglyph('u1CE17', 0x1CE17).boxdrawlight([(0.5,0),(0.5,1-ye),(1,1-ye)])
	f.mkglyph('u1CE18', 0x1CE18).boxdrawlight([(0.5,1),(0.5,ye),(0,ye)])
	f.mkglyph('u1CE19', 0x1CE19).boxdrawlight([(0.5,0),(0.5,1-ye),(0,1-ye)])
	f.mkglyph('u1CE1A', 0x1CE1A).poly((1./3,1), (1./3,0.8), (1,0.4), (1,0.6), (2./3,0.8), (2./3,1))
	f.mkglyph('u1CE1B', 0x1CE1B).poly((1./3,1), (1./3,0.4), (1,0.4), (1,0.6), (2./3,0.6), (2./3,1))
	f.mkglyph('u1CE1C', 0x1CE1C).rect(1./3, 0.4, 2./3, 1)
	f.mkglyph('u1CE1D', 0x1CE1D).poly((1./3,1), (1./3,0.4), (2./3,0.4), (1,0.6), (1,0.8), (2./3,0.6), (2./3,1))
	f.mkglyph('u1CE1E', 0x1CE1E).rect(1./3, 0.4, 1, 0.6)
	f.mkglyph('u1CE1F', 0x1CE1F).rect(0, 0.4, 1, 0.6)
	f.mkglyph('u1CE20', 0x1CE20).poly((0,0.6), (0,0.4), (1,0.4), (1,0.6), (2./3,0.6), (2./3,1), (1./3,1), (1./3,0.6))
	f.mkglyph('u1CE21', 0x1CE21).poly((0,0.6), (0.5,0.9), (1,0.6), (1,0.8), (2./3,1), (1./3,1), (0,0.8))
	f.mkglyph('u1CE22', 0x1CE22).poly((0,0.6), (2./3,1), (1./3,1), (0,0.8))
	f.mkglyph('u1CE23', 0x1CE23).rect(1./3, 0.8, 2./3, 1)
	f.mkglyph('u1CE24', 0x1CE24).poly((0,0.6), (0,0.4), (2./3,0.8), (2./3,1), (1./3,1), (1./3,0.8))
	f.mkglyph('u1CE25', 0x1CE25).rect(0, 0.4, 2./3, 0.6)
	f.mkglyph('u1CE26', 0x1CE26).poly((0,0.8), (0,0.6), (1./3,0.4), (2./3,0.4), (2./3,1), (1./3,1), (1./3,0.6))
	f.mkglyph('u1CE27', 0x1CE27).poly((0,0.6), (0,0.4), (2./3,0.4), (2./3,1), (1./3,1), (1./3,0.6))
	f.mkglyph('u1CE28', 0x1CE28).poly((1./3,1), (1./3,0), (2./3,0), (2./3,0.4), (1,0.4), (1,0.6), (2./3,0.6), (2./3,1))
	f.mkglyph('u1CE29', 0x1CE29).rect(1./3, 0, 2./3, 1)
	f.mkglyph('u1CE2A', 0x1CE2A).poly((1./3,0), (2./3,0), (1,0.2), (1,0.4)).poly((1./3,1), (1,0.6), (1,0.8), (2./3,1))
	f.mkglyph('u1CE2B', 0x1CE2B).poly((1./3,0), (2./3,0), (1,0.2), (1,0.4))
	f.mkglyph('u1CE2C', 0x1CE2C).poly((1./3,1), (1,0.6), (1,0.8), (2./3,1))
	f.mkglyph('u1CE2D', 0x1CE2D).rect(1./3, 0, 2./3, 0.2)
	f.mkglyph('u1CE2E', 0x1CE2E).poly((1./3,0), (2./3,0), (2./3,0.2), (1,0.4), (1,0.6), (2./3,0.8), (2./3,1), (1./3,1), (1./3,0.8), (5./6,0.5), (1./3,0.2))
	f.mkglyph('u1CE2F', 0x1CE2F).poly((0,0.4), (0.5,0.4), (1,0.2), (1,0.4), (0.75,0.5), (1,0.6), (1,0.8), (0.5,0.6), (0,0.6))
	f.mkglyph('u1CE30', 0x1CE30).poly((1./3,0), (2./3,0), (0.5,0.1))
	f.mkglyph('u1CE31', 0x1CE31).poly((2./3,1), (1./3,1), (0.5,0.9))
	f.mkglyph('u1CE32', 0x1CE32).poly((0,0.2), (0.5,0.4), (1,0.2), (1,0.4), (0.75,0.5), (1,0.6), (1,0.8), (0.5,0.6), (0,0.8), (0,0.6), (0.25,0.5), (0,0.4))
	f.mkglyph('u1CE33', 0x1CE33).poly((0,0.2), (0.5,0.5), (1,0.2), (1,0.4), (2./3,0.6), (2./3,1), (1./3,1), (1./3,0.6), (0,0.4))
	f.mkglyph('u1CE34', 0x1CE34).poly((0,0.4), (0.5,0.4), (1,0.2), (1,0.6), (0.5,0.6), (0,0.8))
	f.mkglyph('u1CE35', 0x1CE35).poly((1./3,1), (1./3,0.6), (1,0.2), (1,0.4), (2./3,0.6), (2./3,1))
	f.mkglyph('u1CE36', 0x1CE36).poly((1./3,1), (1./3,0.6), (0,0.6), (0,0.4), (1./3,0.4), (1./3,0), (2./3,0), (2./3,1))
	f.mkglyph('u1CE37', 0x1CE37).poly((1./3,1), (1./3,0.8), (0,0.6), (0,0.4), (1./3,0.2), (1./3,0), (2./3,0), (2./3,0.2), (1./6,0.5), (2./3,0.8), (2./3,1))
	f.mkglyph('u1CE38', 0x1CE38).poly((0,0.2), (1./3,0), (2./3,0), (0,0.4)).poly((0,0.6), (2./3,1), (1./3,1), (0,0.8))
	f.mkglyph('u1CE39', 0x1CE39).poly((1./3,1), (1./3,0.6), (0,0.4), (0,0.2), (1./3,0.4), (1./3,0), (2./3,0), (2./3,1))
	f.mkglyph('u1CE3A', 0x1CE3A).poly((1./3,1), (1./3,0.6), (0,0.6), (0,0.4), (1./3,0.4), (1./3,0), (2./3,0), (2./3,0.4), (1,0.4), (1,0.6), (2./3,0.6), (2./3,1))
	f.mkglyph('u1CE3B', 0x1CE3B).poly((0,0.2), (1./3,0), (2./3,0), (0,0.4))
	f.mkglyph('u1CE3C', 0x1CE3C).rect(1./3, 0, 2./3, 0.6)
	f.mkglyph('u1CE3D', 0x1CE3D).poly((1./3,0), (2./3,0), (2./3,0.4), (1,0.4), (1,0.6), (1./3,0.6))
	f.mkglyph('u1CE3E', 0x1CE3E).poly((1./3,0), (2./3,0), (2./3,0.2), (1,0.4), (1,0.6), (1./3,0.2))
	f.mkglyph('u1CE3F', 0x1CE3F).poly((1./3,0), (2./3,0), (2./3,0.4), (1,0.2), (1,0.4), (2./3,0.6), (1./3,0.6))
	f.mkglyph('u1CE40', 0x1CE40).poly((0,0.4), (1./3,0.4), (1./3,0), (2./3,0), (2./3,0.4), (1,0.4), (1,0.6), (0,0.6))
	f.mkglyph('u1CE41', 0x1CE41).poly((0,0.2), (0.5,0.5), (1,0.2), (1,0.4), (0.5,0.7), (0,0.4))
	f.mkglyph('u1CE42', 0x1CE42).poly((0,0.2), (1./3,0), (2./3,0), (1,0.2), (1,0.4), (0.5,0.1), (0,0.4))
	f.mkglyph('u1CE43', 0x1CE43).poly((0,0.4), (1./3,0.2), (1./3,0), (2./3,0), (2./3,0.2), (0,0.6))
	f.mkglyph('u1CE44', 0x1CE44).poly((0,0.4), (1./3,0.4), (1./3,0), (2./3,0), (2./3,0.6), (0,0.6))
	f.mkglyph('u1CE45', 0x1CE45).poly((0,0), (1./3,0.2), (1./3,0), (2./3,0), (2./3,0.2), (0.5,0.3), (2./3,0.4), (2./3,0.6), (1./3,0.4), (0,0.6), (0,0.4), (1./6,0.3), (0,0.2))
	f.mkglyph('u1CE46', 0x1CE46).poly((0,0.2), (1./3,0.4), (1./3,0), (2./3,0), (2./3,0.6), (1./3,0.6), (0,0.4))
	f.mkglyph('u1CE47', 0x1CE47).rect(1./3, 0.6, 2./3, 1)
	f.mkglyph('u1CE48', 0x1CE48).rect(1./3, 0.2, 2./3, 1)
	f.mkglyph('u1CE49', 0x1CE49).rect(1./3, 0.6, 2./3, 0.8)
	f.mkglyph('u1CE4A', 0x1CE4A).rect(1./3, 0.4, 2./3, 0.8)
	f.mkglyph('u1CE4B', 0x1CE4B).rect(1./3, 0.2, 2./3, 0.8)
	f.mkglyph('u1CE4C', 0x1CE4C).rect(1./3, 0, 2./3, 0.8)
	f.mkglyph('u1CE4D', 0x1CE4D).rect(1./3, 0.4, 2./3, 0.6)
	f.mkglyph('u1CE4E', 0x1CE4E).rect(1./3, 0.2, 2./3, 0.6)
	f.mkglyph('u1CE4F', 0x1CE4F).rect(1./3, 0.2, 2./3, 0.4)
	f.mkglyph('u1CE50', 0x1CE50).rect(1./3, 0, 2./3, 0.4)
	for i in range(1, 64):
		f.mkglyph('u%X' % (0x1CE50 + i), 0x1CE50 + i).sepmap(3, 2, i)
	f.mkglyph('u1CE90', 0x1CE90).rect(0, 0, 0.25, 0.25)
	f.mkglyph('u1CE91', 0x1CE91).rect(0.25, 0, 0.5, 0.25)
	f.mkglyph('u1CE92', 0x1CE92).rect(0.5, 0, 0.75, 0.25)
	f.mkglyph('u1CE93', 0x1CE93).rect(0.75, 0, 1, 0.25)
	f.mkglyph('u1CE94', 0x1CE94).rect(0, 0.25, 0.25, 0.5)
	f.mkglyph('u1CE95', 0x1CE95).rect(0.25, 0.25, 0.5, 0.5)
	f.mkglyph('u1CE96', 0x1CE96).rect(0.5, 0.25, 0.75, 0.5)
	f.mkglyph('u1CE97', 0x1CE97).rect(0.75, 0.25, 1, 0.5)
	f.mkglyph('u1CE98', 0x1CE98).rect(0, 0.5, 0.25, 0.75)
	f.mkglyph('u1CE99', 0x1CE99).rect(0.25, 0.5, 0.5, 0.75)
	f.mkglyph('u1CE9A', 0x1CE9A).rect(0.5, 0.5, 0.75, 0.75)
	f.mkglyph('u1CE9B', 0x1CE9B).rect(0.75, 0.5, 1, 0.75)
	f.mkglyph('u1CE9C', 0x1CE9C).rect(0, 0.75, 0.25, 1)
	f.mkglyph('u1CE9D', 0x1CE9D).rect(0.25, 0.75, 0.5, 1)
	f.mkglyph('u1CE9E', 0x1CE9E).rect(0.5, 0.75, 0.75, 1)
	f.mkglyph('u1CE9F', 0x1CE9F).rect(0.75, 0.75, 1, 1)
	f.mkglyph('u1CEA0', 0x1CEA0).rect(0.5, 0.75, 1, 1)
	f.mkglyph('u1CEA1', 0x1CEA1).rect(0.25, 0.75, 1, 1)
	f.mkglyph('u1CEA2', 0x1CEA2).rect(0, 0.75, 0.75, 1)
	f.mkglyph('u1CEA3', 0x1CEA3).rect(0, 0.75, 0.5, 1)
	f.mkglyph('u1CEA4', 0x1CEA4).rect(0, 0.5, 0.25, 1)
	f.mkglyph('u1CEA5', 0x1CEA5).rect(0, 0.25, 0.25, 1)
	f.mkglyph('u1CEA6', 0x1CEA6).rect(0, 0, 0.25, 0.75)
	f.mkglyph('u1CEA7', 0x1CEA7).rect(0, 0, 0.25, 0.5)
	f.mkglyph('u1CEA8', 0x1CEA8).rect(0, 0, 0.5, 0.25)
	f.mkglyph('u1CEA9', 0x1CEA9).rect(0, 0, 0.75, 0.25)
	f.mkglyph('u1CEAA', 0x1CEAA).rect(0.25, 0, 1, 0.25)
	f.mkglyph('u1CEAB', 0x1CEAB).rect(0.5, 0, 1, 0.25)
	f.mkglyph('u1CEAC', 0x1CEAC).rect(0.75, 0, 1, 0.5)
	f.mkglyph('u1CEAD', 0x1CEAD).rect(0.75, 0, 1, 0.75)
	f.mkglyph('u1CEAE', 0x1CEAE).rect(0.75, 0.25, 1, 1)
	f.mkglyph('u1CEAF', 0x1CEAF).rect(0.75, 0.5, 1, 1)
	# Output SFD.
	f.output()


def help(file=sys.stderr):
	print('slcgen - generate fontforge file of symbols for legacy computing', file=file)
	print('', file=file)
	print('Options:', file=file)
	print(' -a <int>    ascent in em units', file=file)
	print(' -d <int>    descent in em units', file=file)
	print(' -w <int>    advance width in em units', file=file)
	print(' -ph <int>   height of medium shade characters in pixels', file=file)
	print(' -pw <int>   width of medium shade characters in pixels', file=file)
	print(' -df <float> weight of lines in diagonal fill characters in em units', file=file)
	print(' -ds <float> weight of spaces in diagonal fill characters in em units', file=file)
	print(' -da <float> angle of diagonal fill characters in degrees (0-90)', file=file)
	print(' -bl <int>   line weight of light box drawing characters in em units', file=file)
	print(' -bh <int>   line weight of heavy box drawing characters in em units', file=file)
	print(' -bg <int>   gap in double box drawing characters in em units', file=file)
	print(' -br <int>   radius of arc box drawing characters in em units', file=file)
	print(' -bt <str>   line ending style of box drawing characters: "truncate" or "cute"', file=file)
	print(' -st <int>   top padding of separated block mosaic characters in em units', file=file)
	print(' -sr <int>   right padding of separated block mosaic characters in em units', file=file)
	print(' -sb <int>   bottom padding of separated block mosaic characters in em units', file=file)
	print(' -sl <int>   left padding of separated block mosaic characters in em units', file=file)
	print(' -sv <int>   equivalent to both -st and -sb (vertical padding)', file=file)
	print(' -sh <int>   equivalent to both -sr and -sl (horizontal padding)', file=file)
	print(' -sp <int>   equivalent to all of -st, -sr, -sb, -sl', file=file)
	print(' -o <path>   path to output file (default is out.sfd)', file=file)


def main():
	kwargs = {}
	currentFlag = None
	for arg in sys.argv[1:]:
		try:
			if currentFlag is None:
				if arg.startswith('-'):
					currentFlag = arg
					continue
				else:
					help()
					return
			elif currentFlag == '-a':
				kwargs['ascent'] = abs(int(arg))
			elif currentFlag == '-d':
				kwargs['descent'] = abs(int(arg))
			elif currentFlag == '-w':
				kwargs['width'] = abs(int(arg))
			elif currentFlag == '-ph':
				kwargs['pixelHeight'] = abs(int(arg))
			elif currentFlag == '-pw':
				kwargs['pixelWidth'] = abs(int(arg))
			elif currentFlag == '-da':
				kwargs['diagonalFillAngle'] = abs(float(arg))
			elif currentFlag == '-df':
				kwargs['diagonalFillWeight'] = abs(float(arg))
			elif currentFlag == '-ds':
				kwargs['diagonalSpaceWeight'] = abs(float(arg))
			elif currentFlag == '-bl':
				kwargs['boxLightWeight'] = abs(int(arg))
			elif currentFlag == '-bh':
				kwargs['boxHeavyWeight'] = abs(int(arg))
			elif currentFlag == '-bg':
				kwargs['boxDoubleGap'] = abs(int(arg))
			elif currentFlag == '-br':
				kwargs['boxArcRadius'] = abs(int(arg))
			elif currentFlag == '-bt':
				if arg == 'truncate':
					kwargs['boxLineTruncate'] = True
				elif arg == 'cute':
					kwargs['boxLineTruncate'] = False
				else:
					help()
					return
			elif currentFlag == '-st':
				kwargs['separationTop'] = abs(int(arg))
			elif currentFlag == '-sr':
				kwargs['separationRight'] = abs(int(arg))
			elif currentFlag == '-sb':
				kwargs['separationBottom'] = abs(int(arg))
			elif currentFlag == '-sl':
				kwargs['separationLeft'] = abs(int(arg))
			elif currentFlag == '-sv':
				kwargs['separationTop'] = abs(int(arg))
				kwargs['separationBottom'] = abs(int(arg))
			elif currentFlag == '-sh':
				kwargs['separationRight'] = abs(int(arg))
				kwargs['separationLeft'] = abs(int(arg))
			elif currentFlag == '-sp':
				kwargs['separationTop'] = abs(int(arg))
				kwargs['separationRight'] = abs(int(arg))
				kwargs['separationBottom'] = abs(int(arg))
				kwargs['separationLeft'] = abs(int(arg))
			elif currentFlag == '-o':
				kwargs['file'] = arg
			else:
				help()
				return
			currentFlag = None
			continue
		except ValueError:
			help()
			return
	if len(kwargs) == 0 or currentFlag is not None:
		help()
		return
	slcgen(**kwargs)


if __name__ == '__main__':
	main()
