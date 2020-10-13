#!/usr/bin/env python
# 
# NAME: sliceProds.python
# 
# PURPOSE:  Separate list in many pieces according a scheme
# 
###############################################################################
import re,sys,os

prodlists = [ ['Prod3_LaPalma_Baseline_NSB1x_gamma_South_20deg_DL0.list',[10,10,80]],
              ['Prod3_LaPalma_Baseline_NSB1x_proton_South_20deg_DL0.list',[40,60]],
              ['Prod3_LaPalma_Baseline_NSB1x_electron_South_20deg_DL0.list',[100]] ]

debug = False

for prodlist in prodlists: 
  flist = open(prodlist[0],"r")
  prodLines = flist.readlines()
  flist.close()

  numlines = [1,]

  if debug:
    print "DEBUG>> prodlist[1][:len(prodlist[1])-1]:",prodlist[1][:len(prodlist[1])-1]

  for prop in prodlist[1][:len(prodlist[1])-1]:
    delta = int(prop / 100. * len(prodLines) +.5)
    numlines.append( numlines[-1]+delta ) 

  print prodlist[0],":", numlines

  for inum,iprop in enumerate(numlines):

    outfic = re.sub(r"(.*)\.(.*)",r"\1-"+str(inum+1)+r".\2",prodlist[0])
    if debug:
      print "DEBUG>> outfic:",outfic
     
    if inum+1<len(numlines):
      Tlines = prodLines[iprop:numlines[inum+1]]
    else:
      Tlines = prodLines[iprop:]
      
    if debug:
      print "DEBUG>> len(Tlines):",len(Tlines)
    if len(Tlines) > 0:
      fprop = open(outfic,"w")
      for line in Tlines:
        print >>fprop, line.strip()
      fprop.close()  
