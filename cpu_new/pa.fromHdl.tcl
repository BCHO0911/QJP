
# PlanAhead Launch Script for Pre-Synthesis Floorplanning, created by Project Navigator

create_project -name cpu -dir "C:/Users/feiniaohuang/Desktop/cpu/cpu/planAhead_run_2" -part xc3s1200efg320-4
set_param project.pinAheadLayout yes
set srcset [get_property srcset [current_run -impl]]
set_property target_constrs_file "cpu.ucf" [current_fileset -constrset]
set hdlfile [add_files [list {cpu.vhd}]]
set_property file_type VHDL $hdlfile
set_property library work $hdlfile
set_property top cpu $srcset
add_files [list {cpu.ucf}] -fileset [get_property constrset [current_run]]
open_rtl_design -part xc3s1200efg320-4
