#!/usr/bin/env bash

#d="${1}"
#sdir="${d}sweep"
sdir="$1"
out="fig/${sdir}.html"

html_header() {
  cat << __EOF
    <html>
     <head>
      <style>
        .floated {
          position: relative;
          float: left;
        }
        .img_tag {
          position: absolute;
          top: 0;
          left: 0;
          z-index: 1;
        }

        .floated img{
          position: relative;
          z-index: 5;
        }
      </style>
     </head>
     <body>
__EOF
}

html_footer() {
  cat << __EOF
   </body>
    </html>
__EOF
}

html_figure() {
  rec="${sdir}/${1##*/}"
  cat << __EOF
    <div class="floated">
      <div class="img_tag">${rec}</div>
      <img src="$rec"></a>
    </div>
__EOF
}

: > "$out"
html_header >> "$out"
if [[ "$sdir" =~ "example1_decreasing" ]]                     || \
   [[ "$sdir" =~ "example2_decreasing" ]]; then
  for png in $(
    find fig/${sdir} -type f -iname '*.png' -exec basename {} \; \
      | rsort
    ); do
    html_figure "$png" 
  done >> "$out"
elif [[ "$sdir" =~ "example1_increasing" ]]  || \
     [[ "$sdir" =~ "example2_increasing" ]]; then
  for png in $(
    find fig/${sdir} -type f -iname '*.png' -exec basename {} \; \
      | rsort | tac
    ); do
    html_figure "$png" 
  done >> "$out"
fi
html_footer >> "$out"
