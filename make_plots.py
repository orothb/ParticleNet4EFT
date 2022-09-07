import ROOT
import sys
from time import sleep
from tqdm import tqdm

def sethistogramstyle (hx, lcolor=1):
    hx.SetTitle("")
    hx.SetStats(0)
    hx.GetXaxis().SetTitleSize(0.045)
    hx.GetXaxis().SetLabelSize(0.045)
    hx.GetYaxis().SetTitleSize(0.045)
    hx.GetYaxis().SetLabelSize(0.045)
    hx.SetLineColor(lcolor)
    hx.SetMarkerColor(lcolor)
    #return hx	

def setgraphstyle (gr, lcolor=1):
    gr.SetTitle("")
    gr.GetXaxis().SetTitleSize(0.04)
    gr.GetXaxis().SetLabelSize(0.04)
    gr.GetXaxis().SetTitleOffset(1.15)
    gr.GetYaxis().SetTitleSize(0.04)
    gr.GetYaxis().SetLabelSize(0.04)
    gr.GetYaxis().SetTitleOffset(1.25)
    gr.SetLineColor(lcolor)
    gr.SetMarkerColor(lcolor)

label_list=["label_quad_0","label_quad_1","label_quad_2","label_quad_3"]
label_title=["label_quad_0","label_quad_1","label_quad_2","label_quad_3"]
col=[1,2,(416+2),4,6,(400+2)]
sig_list=[ROOT.TH1F('h_'+label, label, 50, 0, 1) for label in label_list]
bkg_list=[ROOT.TH1F('b_'+label, label, 50, 0, 1) for label in label_list]

score_list=[] #"score_label_Muon_Prompt", "score_label_Muon_unknown", "score_label_Muon_fromHFHadron", "score_label_Muon_fromLFHadron", "score_label_Muon_fromTau", "score_label_Muon_fromPhoton"]
for label in label_list:
    score_list.append("score_"+label)
#used_list=label_list[1:6]
fl = ROOT.TFile.Open(sys.argv[1])
tree = fl.Get("Events")

for ievt in tqdm(range(tree.GetEntries())):
    tree.GetEntry(ievt)
    if getattr(tree, label_list[0]):
        for label in range(len(label_list)):
            x=getattr(tree, score_list[0])
            y=getattr(tree, score_list[label])
            filler=x/(x+y)
            sig_list[label].Fill(filler)
    else:
        for label in range(len(label_list)):
            if getattr(tree, label_list[label]):
                x=getattr(tree, score_list[0])
                y=getattr(tree, score_list[label])
                filler=x/(x+y)
                bkg_list[label].Fill(filler)
fl.Close()

ROOT.gROOT.SetBatch(True)

gr_ROCs, gr_sigeffs, gr_bkgeffs = [], [], []

canv_scores=[ROOT.TCanvas("c_"+label,"c",800,600) for label in label_list]

for label in range(len(label_list)):

	canv_scores[label].cd()
	ROOT.gPad.SetLogy(1)

	leg=ROOT.TLegend (.25,.7,.45,.875)
	leg.SetBorderSize(0)

    	sig_list[label].SetStats(0)
    	sig_list[label].Scale(1./sig_list[label].Integral())
    	bkg_list[label].SetStats(0)
        bkg_list[label].Scale(1./max(1.e-6,bkg_list[label].Integral()))

	sethistogramstyle(sig_list[label],2)
	sethistogramstyle(bkg_list[label],4)

	sig_list[label].GetXaxis().SetTitle("score "+label_title[0]+" / (score "+label_title[0]+" + score "+label_title[label]+")")

	sig_list[label].Draw("hist")
	bkg_list[label].Draw("hist:SAME")

    	leg.AddEntry(sig_list[label], label_title[0], "l")
	leg.AddEntry(bkg_list[label], label_title[label], "l")
	leg.Draw("SAME")

	canv_scores[label].SaveAs("scores_"+label_list[label]+".png")

	gr_roc = ROOT.TGraph(sig_list[label].GetNbinsX());
	gr_sig = ROOT.TGraph(sig_list[label].GetNbinsX());
	gr_bkg = ROOT.TGraph(sig_list[label].GetNbinsX());

	for bn in range(sig_list[label].GetNbinsX()):
	    sig_eff = sig_list[label].Integral(bn,sig_list[label].GetNbinsX())
	    bkg_eff = bkg_list[label].Integral(bn,bkg_list[label].GetNbinsX())

	    gr_roc.SetPoint(bn+1,sig_eff,bkg_eff);
	    gr_sig.SetPoint(bn+1,sig_list[label].GetBinLowEdge(bn+1),sig_eff)
	    gr_bkg.SetPoint(bn+1,sig_list[label].GetBinLowEdge(bn+1),bkg_eff);

	gr_ROCs.append(gr_roc)
	gr_sigeffs.append(gr_sig)
	gr_bkgeffs.append(gr_bkg)

for icanv in range(3):

    roc_canv = ROOT.TCanvas("roc", "roc", 50, 50, 800, 800)
    roc_canv.cd()
    ROOT.gPad.SetGridy(1)
    ROOT.gPad.SetGridx(1)
    #ROOT.gPad.SetLogy(1)

    roc_leg = ROOT.TLegend(0.15,0.4,0.45,0.7)
    roc_leg.SetBorderSize(0)
    roc_leg.SetTextSize(0.04)

    for i in range(1,len(label_list)):

        if icanv==0:
            pgr = gr_sigeffs[i]
        elif icanv==1:
            pgr = gr_bkgeffs[i]
        else:
            ROOT.gPad.SetLogy(1)
            pgr = gr_ROCs[i]

        setgraphstyle(pgr,col[i])

        if icanv==0:
            pgr.GetXaxis().SetTitle("MVA score")
            pgr.GetYaxis().SetTitle("Signal efficiency")
        elif icanv==1:
            pgr.GetXaxis().SetTitle("MVA score")
            pgr.GetYaxis().SetTitle("Background mistag rate")
        else:
            pgr.GetXaxis().SetTitle("Signal efficiency")
            pgr.GetYaxis().SetTitle("Background mistag rate")
            pgr.SetMinimum(5.e-3)
            pgr.GetXaxis().SetRangeUser(0.9,1.0);

        if i == 1:
            pgr.Draw("AL")
        else:
            pgr.Draw("L:SAME")

        roc_leg.AddEntry(pgr, label_title[i], "L")

    roc_leg.Draw("sames")

    if icanv==0:
        roc_canv.SaveAs("SignalEfficiency.png")
    elif icanv==1:
        roc_canv.SaveAs("BackgroundEfficiency.png")
    else:
        roc_canv.SaveAs("ROC.png")

    roc_canv.Close()
    ROOT.gSystem.ProcessEvents()
del roc_canv
