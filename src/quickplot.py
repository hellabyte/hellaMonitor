#!/usr/bin/env python
"""
This is an investigation specific plotting file that was made on the
fly.

It requires updates and greater portability.

In general: it generates a timeseries plot for various fields on a
single figure. 

The changes to this file could either make it more general, or more
specific to a new investigation.
"""
import sys,os
from hellaPy import *
from pylab import *
from numpy import *
from glob import glob
from matplotlib.cbook import get_sample_data
import multiprocessing as mp

NPROCS=1

HEADER_OFFSET=256

NUM_COLS=18
NUM_TS_FP_BASE=100

REPLOT_PLOTTED=False

FIG_PATH = 'fig/'

NRG_PLOT = True
if len(sys.argv) > 3:
  NRG_PLOT = False

if not os.path.exists(FIG_PATH):
  os.mkdir(FIG_PATH)

subdir = sys.argv[1].split('/')[-2] + sys.argv[2]

def get_field_fig(prefix):
  f_figs = [None,None]
  try:
    path = 'fig/{:s}sweep/field/{:s}*.png'.format(subdir,prefix)
    f_figs_glob= glob(path)
    f_figs_glob.sort()
    f_figs = [ os.path.abspath(f_figs_glob[k]) for k in [0,-1] ]
  except Exception as ex:
    print('exception: ', ex.args)
  return f_figs

def parse_prefix(prefix,token):
  parsed=prefix.split(token)[1].split('_')[0].lower()
  print('{:3s} : {:10s} : {:s}'.format(token,parsed,prefix))
  return parsed

def get_float_from_sci(sci):
  exp_not = 'e' if 'e' in sci else 'd'
  if 'd' not in sci and exp_not =='d':
    print('Invalid Sci Notation: {:s}'.format(sci))
    sys.exit(1)
  base,power = [float(s) for s in sci.split(exp_not)]
  decimal    = base*10**power
  return decimal

def update_plot(f,p):
  """
    If ts data file (f) is newer than plot file (p), then return True 
    (plotting should be done).
  """
  val=REPLOT_PLOTTED
  if not os.path.exists(p):
    val  = True
  elif not REPLOT_PLOTTED:
    f_mt = os.path.getmtime(f)
    p_mt = os.path.getmtime(p)
    val  = True if f_mt >= p_mt else False
  return val

def ma(x,N):
  cs = cumsum(r_[0,x])
  return (cs[N:]-cs[:-N])/N

def main(f):
  prefix    = f.split('/')[-1]
  if '_B' in prefix:
    omega_str = parse_prefix(prefix,'_B')
    Re_nu_str = parse_prefix(prefix,'_N')
    alpha_str = parse_prefix(prefix,'_F')
  else:
    omega_str = parse_prefix(prefix,'_o')
    Re_nu_str = '2e4'
    alpha_str = parse_prefix(prefix,'_a')
  mesh_str  = parse_prefix(prefix,'_m')
  tr_str    = parse_prefix(prefix,'_tr')
  NUM_TS_FP = NUM_TS_FP_BASE * int(tr_str[0])
  if 'sqrt2' in omega_str:
    omega_str = r'$\sqrt{2}$'
    NUM_TS_FP = NUM_TS_FP_BASE * 10
    omega     = sqrt(2)
  else:
    omega     = get_float_from_sci(omega_str)
  Re_nu     = get_float_from_sci(Re_nu_str)
  alpha     = get_float_from_sci(alpha_str)
  mesh      = int(mesh_str)
  tr        = int(get_float_from_sci(tr_str))

  Tau   = 2*pi/(omega*Re_nu)
  #f_figs= get_field_fig(prefix)
  outdir= '{:s}{:s}/'.format(FIG_PATH,subdir)
  out   = '{:s}{:s}.png'.format(outdir,prefix)
  if not os.path.exists(outdir):
    os.mkdir(outdir)
  replot_bool = update_plot(f,out)
  if replot_bool:
    print('Parsing {:s}'.format(f))
    d     = array(memmap(f,dtype=double,offset=HEADER_OFFSET)).copy()
    t     = d[0::NUM_COLS]
    E     = d[1::NUM_COLS]
    ET    = d[2::NUM_COLS]*24
    u     = d[4::NUM_COLS]
    uM,um = u.max(),u.min()
    vM,vm = -20,-30
    u     = vm + (vM-vm)/(uM-um) * (u-um)
    u     = u[::NUM_TS_FP]
    Kx    = d[13::NUM_COLS]
    Kz    = d[14::NUM_COLS]
    Qp    = d[16::NUM_COLS]
    dt    = t[1]-t[0]
    taus  = t/Tau
    figure(1,figsize=(10,5)); clf()
    if not NRG_PLOT:
      print('Plotting thermal energy {:s}'.format(f))
      plot(taus-taus[0],ET,'k-')
      xlabel(r'Number of Forcing Periods')
      ylabel(r'$E_T$')
      ts  = array([ q[0]    for q in split(taus-taus[0],arange(0,len(ET),NUM_TS_FP))[1:-1] ])[1:]
      ETs = array([ q.max() for q in split(ET,arange(0,len(ET),NUM_TS_FP))[1:-1] ])
      dETs= abs(diff(ETs))/ETs[-1]
      ax2 = gca().twinx()
      ax2.semilogy(ts,dETs,'ro-',zorder=-10)
      figtext(.97,.5,r'$\varepsilon_{R,E_T}$',color='r',rotation=90,fontsize=20)
    else:
      print('Plotting energy {:s}'.format(f))
      plot(taus,log10(E),'k-')
      print('Plotting velocity strobe {:s}'.format(f))
      plot(taus[::NUM_TS_FP][:len(u)],u,'o',mfc='#777777',alpha=.3,mew=0,ms=3)
      xlabel(r'Number of Forcing Periods ($t/\tau$)')
      ylabel(r'$E$')
      ylim(-32,7)
      yticks([-30,-20,-10,0])
      grid(which='major',axis='both',linestyle='--',color='#777777')
      grid(which='minor',axis='both',linestyle=':' ,color='#777777')
      print('Plotting antisym {:s}'.format(f))
      ts = array([ q[0]    for q in split(taus,arange(0,len(E),NUM_TS_FP))[1:-1] ])[1:]
      Es = array([ q.max() for q in split(E,arange(0,len(E),NUM_TS_FP))[1:-1] ])
      dEs= abs(diff(Es))/Es[-1]
      ax2 = gca().twinx()
      if not 'kxz' in prefix.lower():
        ax2.plot(taus,log10(Kx),'r-',alpha=.3)
        ax2.plot(taus,log10(Kz),'b-',alpha=.3)
      ax2.plot(taus,log10(Qp), '-' ,c='#00BC87',alpha=.3)
      ax2.plot(  ts,log10(dEs),'-o',c='#AE00FF',alpha=.8,ms=.1)
      ax2.set_ylim(-32,7)
      ax2.set_yticks([-30,-20,-10,0])
      figtext(.97,.50,r'$K_x T$',color='r',rotation=90,fontsize=20)
      figtext(.97,.75,r'$K_z T$',color='b',rotation=90,fontsize=20)
      figtext(.97,.25,r'$Q_\pi T$',color='#00BC87',rotation=90,fontsize=20)
      figtext(.69,.50,r'$\varepsilon_{R,E}$',color='#AE00FF',alpha=.8,fontsize=20)
      figtext(.69,.33,r'not-to-scale $u_\chi$',color='k',alpha=.5,fontsize=20)
      # Plots flow in corner
      #ffsopt = [
      #  {
      #    'axes'   : [0,0,.25,.25],         
      #    'anchor' : 'SW',
      #  },
      #  {
      #    'axes'   : [.75,0,.25,.25],         
      #    'anchor' : 'SE',
      #  },
      #]
      #for k,f_fig in enumerate( f_figs ):
      #  ffopt = ffsopt[k]
      #  if f_fig != None:
      #    im = imread(get_sample_data(f_fig))
      #    fig= gcf()
      #    newax = fig.add_axes(ffopt['axes'],anchor=ffopt['anchor'])
      #    newax.imshow(im)
      #    newax.axis('off')
    al_fwide= int(alpha_str.split('-')[-1])
    if 'sqrt' in omega_str:
      tstr = (
                r"$\omega=$ {omega:s} "
                r"$\alpha=$ {alpha:.{awidth}f} "
                r"$Mesh=$ {mesh:d} "
                r"$\Delta t=\tau/$ {tr:d}"
             ).format(
                        omega=omega_str,
                        alpha=alpha,
                        mesh=mesh,
                        tr=tr,
                        awidth=al_fwide
      )
    else:
      om_fwide= int(omega_str.split('-')[-1])
      tstr = (
                r"$\omega=$ {omega:.{owidth}f} "
                r"$\alpha=$ {alpha:.{awidth}f} "
                r"$Mesh=$ {mesh:d} "
                r"$\Delta t=\tau/$ {tr:d}"
             ).format(
                        omega=omega,
                        alpha=alpha,
                        mesh=mesh,
                        tr=tr,
                        owidth=om_fwide,
                        awidth=al_fwide
      )
    title(tstr)
    tick_params('both',which='both',direction='in')
    savefig(out)
  else:
    print('Skipping {:s}'.format(f))
  return None

if __name__ == '__main__':
  if NPROCS > 1:
    check_files = glob(sys.argv[1])
    check_files.sort()
    pool = mp.Pool(processes=NPROCS)
    pool.map(main,check_files)
  else:
    #check_files = sys.argv[1]
    #for record in check_files:
    # main(record)
    record = sys.argv[1]
    prefix = record.split('/')[-1]
    outdir= '{:s}{:s}/'.format(FIG_PATH,subdir)
    out   = '{:s}{:s}.png'.format(outdir,prefix)
    if not os.path.exists(outdir):
      os.mkdir(outdir)
    if update_plot(record,out):
      main(record)
    else:
      print('Skipping {:s}'.format(out))

