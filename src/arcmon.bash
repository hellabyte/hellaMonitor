#!/usr/bin/env bash
# ======================================================================
# arcmon.bash
#   Script for archiving and monitoring timeseries data
# ----------------------------------------------------------------------
# Currently, specify simulation to archive and monitor in script rather
# than from config file.
#
# Todo: Pass a config file to specify simulation to archive and monitor
#
# ======================================================================

# Generate arrays of compute nodes
mapfile -t c6 < var/compute_nodes6
mapfile -t c4 < var/compute_nodes4
# Collect compute nodes into single array
compute_nodes=(1 3 5 7 ${c6[@]} ${c4[@]} )

# Temporary sorting files
tmp_foo="/tmp/arcmon_monitor_list.txt"
tmp_sorted_foo="/tmp/arcmon_sorted_monitor_list.txt"

trapped() {
  printf "Trapped -- QUITTING\n"
  exit 150
}

trap trapped 1 2 3 4 5 6 7 8

RSYNC_OPTS=(
  -av 
  --progress 
  -e "ssh -o ConnectTimeout=5"
  --exclude="lib/" 
  --exclude="bin/"
)

SLEEP_TIME=30m

collect_updated() {
  # --------------------------------------------------------------------
  # This function is for the monitor -- this function filters archived
  # simulations that have already been monitored but have not been
  # updated yet. This prevents wasting cycles on unchanged data.
  # --------------------------------------------------------------------
  # Collect
  in_rec="$1"
  sub_dir="$2"
  prefix=$(basename "$in_rec")
  out_rec="${sub_dir}_monitor/${prefix}.png"
  if [[ "$sub_dir" =~ "monitor"  ]]; then
    out_rec="${sub_dir}/${prefix}.png"
  fi
  # If out record does not exist or input is newer than output, then
  # operate
  if ! [[ -e "$out_rec" ]] || [[ "$in_rec" -nt "$out_rec" ]]; then
    printf "$in_rec\n"
  fi
}

# array of simulation projects
projs=(
  example_project
)
# path prefix for archive
repo=/media/archive_disk/investigation/timeseries_data
# associative array for simulation archive directory
declare -AA proj_dir
for proj in ${projs[@]}; do
  pdir="${repo}/${proj}"
  proj_dir[$proj]="$pdir"
  # ensure that simulation archive directory exists
  ! [[ -d "$pdir" ]] && mkdir -pv "$pdir" || : 
done

# export the collect_updated function so gnu-parallel may use it
export -f collect_updated

# main loop 
while true; do 
  # archive simulations from filtered compute nodes
  for compute_node in ${compute_nodes[@]}; do 
    printf "$compute_node\n"
    rsync "${RSYNC_OPTS[@]}"                     \
      mathe$n:~/.local/src/d2zv/${projs[0]}/ts_* \
      ${proj_dir[${projs[0]}]}/
  done
  
  # generate or clean temporary collection file
  : > "$tmp_foo"
  printf 'parsing data files\n'

  # determine which files require updated monitors
  for proj in ${projs[@]}; do
    proj_recs="${proj_dir[$proj]}/ts_*"
    parallel -j2 --lb --will-cite collect_updated {1} "fig/$proj"    \
      ::: ${proj_recs[@]} \
      >>  "$tmp_foo"
  done

  # sort collection file
  sort -V "$tmp_foo" > "$tmp_sorted_foo"

  # generate monitor plots for files that were updated
  printf 'plotting data files\n'

  parallel -j2 --lb --will-cite python src/quickplot.py {1} _monitor \
    :::: "$tmp_sorted_foo"                                           \
    > var/sweep_monitor.log

  # generate html pages for requested projects
  printf 'html gen\n'
  parallel -j2 --lb --will-cite bash src/quickplot_html.bash "{}_monitor" ::: ${projs[@]}

  # transer monitor files to web host
  rsync -r "${RSYNC_OPTS[@]}" \
    fig/*                     \
    mathpost:~/public_html/monitor
  date '+---%T---\n'

  # wait to archive and monitor again
  sleep $SLEEP_TIME
  rm "$tmp_foo" "$tmp_sorted_foo"
done

