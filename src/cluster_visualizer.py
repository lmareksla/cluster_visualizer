import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import customtkinter as ctk
from tkinter import ttk
import sys
import os
import pandas as pd
import copy
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'dpe/src/'))
from cluster import Cluster
from clist import Clist


class ClusterVisualuzerGUI(object):

    """docstring for ClusterVisualuzerGUI"""
    def __init__(self, root):
        super(ClusterVisualuzerGUI, self).__init__()

        self.version = 1.2
        self.date = 231015
        self.print_info()

        # ---------------------------------------------

        self.theme = "light"

        ctk.set_appearance_mode(self.theme)
        ctk.set_default_color_theme("dark-blue")

        root.geometry("1600x950")

        # configure grid layout (4x4)
        root.grid_columnconfigure((0, 1, 2), weight=0)
        root.grid_rowconfigure((0, 1), weight=1)

        self.color_code_bcl = '#242424'
        if self.theme == "light": 
            self.color_code_bcl = '#EBEBEB'
            self.color_code_bcl_fr = '#DBDBDB'

        self.root = root
        self.root.title("Cluster Visualizer")

        # ---------------------------------------------

        self.file_in_path = ""

        self.clist = None
        self.clist_ok = None
        self.clist_out = None
        self.clist_orig = None  # original clist for restoration
        self.file_clist_path = ""
        self.file_clist = None

        self.cluster_count_max = 10000
        self.clist_use_extension = False

        self.hist1d_log_x = False
        self.hist1d_log_y = False
        self.hist1d_curr_var = "E"
        self.hist1d_keep_same_bins = True
        self.hist1d_history = {}

        self.var_hist2d_x = "E"
        self.var_hist2d_y = "Size"

        self.show_clist_ok = True

        self.cluster_curr = None
        self.cluster_id_curr = 0
        self.cluster_par_curr_idx = 4
        self.cluster_par_list = []

        self.clusters_count_show = 30
        self.clusters_curr_start = 0
        self.clusters_batch_curr = 1

        self.clusters_count_ok = 0
        self.clusters_count_out = 0

        self.scrollable_frame_switches = []
        self.filter_entries = []  
        self.filters_prev = []
        self.file_filter_ini_path = ""
        self.file_filter_ini = None
        self.filters_curr = []

        # ---------------------------------------------    
        # hist1d visualizer 0x0
        # ---------------------------------------------  
        
        self.frame_hist1d = ctk.CTkFrame(self.root, fg_color=self.color_code_bcl)
        self.frame_hist1d.grid(row=0, column=0, sticky="nsew")
        self.frame_hist1d.grid_rowconfigure((0, 1, 2), weight=0)
        self.frame_hist1d.grid_columnconfigure((0, 1, 2, 3), weight=0)
        row_shift_hist1d = 0

        self.swch_hist1d_log_y = ctk.CTkSwitch(self.frame_hist1d, text="log y", state="normal",
                                                command=self.switch_hist1d_log_y)
        self.swch_hist1d_log_y.grid(row=row_shift_hist1d, column=0)
        self.swch_hist1d_log_x = ctk.CTkSwitch(self.frame_hist1d, text="log x", state="normal",
                                                command=self.switch_hist1d_log_x)
        self.swch_hist1d_log_x.grid(row=row_shift_hist1d, column=1) 
        self.swch_hist_same_bin = ctk.CTkSwitch(self.frame_hist1d, text="same bins", state="normal",
                                                command=self.switch_to_keep_same_hist1d_bin)
        self.swch_hist_same_bin.select()
        self.swch_hist_same_bin.grid(row=row_shift_hist1d, column=2, sticky="e")  
        self.cbox_hist1d = ctk.CTkComboBox(self.frame_hist1d, values=[""], command=self.show_hist1d)
        self.cbox_hist1d.grid(row=row_shift_hist1d, column=3)
        row_shift_hist1d += 1  

        self.fig_hist1d, self.ax_hist1d = plt.subplots(figsize=(5, 4))
        self.fig_hist1d.set_facecolor( self.color_code_bcl) #  #EBEBEB 
        self.fig_hist1d.set_layout_engine(layout="tight")        
        self.colorbar_hist1d = None
        self.canvas_hist1d = FigureCanvasTkAgg(self.fig_hist1d, master=self.frame_hist1d)
        self.canvas_hist1d.get_tk_widget().grid(row=row_shift_hist1d, column=0, columnspan=4)  
        self.canvas_hist1d.draw()        
        row_shift_hist1d += 1  

        self.toolbar_frame = ctk.CTkFrame(self.frame_hist1d)        
        self.toolbar_frame.grid(row=row_shift_hist1d, column=0, columnspan=4)
        self.toolbar = NavigationToolbar2Tk(self.canvas_hist1d, self.toolbar_frame)
        self.toolbar.config(background="#EBEBEB")
        self.toolbar._message_label.config(background="#EBEBEB")
        for button in self.toolbar.winfo_children():
            button.config(background="#EBEBEB")        
        self.toolbar.update()  # Update the toolbar to reflect actions
        row_shift_hist1d += 1  

        # ---------------------------------------------    
        # cluster visualizer 1x0
        # ---------------------------------------------    

        self.frame_cluster = ctk.CTkFrame(self.root, fg_color=self.color_code_bcl)
        self.frame_cluster.grid(row=1, column=0, sticky="nsew")
        self.frame_cluster.grid_rowconfigure((0, 1, 2), weight=0)
        self.frame_cluster.grid_columnconfigure((0, 1, 2, 3), weight=0)
        row_shift_cluster = 0

        self.bt_prev_cluster = ctk.CTkButton(self.frame_cluster, text="<", command=self.show_prev_cluster)
        self.bt_prev_cluster.grid(row=row_shift_cluster, column=0)  
        self.lbl_cluster_num = ctk.CTkLabel(self.frame_cluster, text="-")
        self.lbl_cluster_num.grid(row=row_shift_cluster, column=1)  
        # self.en_cluster_num = ctk.CTkEntry(self.frame_cluster, placeholder_text = f"{self.cluster_id_curr}")
        # self.en_cluster_num.grid(row=row_shift_cluster, column=1)      
        # self.en_cluster_num.bind('<Enter>', self.show_cluster)
        self.bt_next_cluster = ctk.CTkButton(self.frame_cluster, text=">", command=self.show_next_cluster)
        self.bt_next_cluster.grid(row=row_shift_cluster, column=2)
        self.cbox_cluster = ctk.CTkComboBox(self.frame_cluster, values=[""], command=self.set_cluster_par_curr_idx)
        self.cbox_cluster.set("Cluster parameters") 
        self.cbox_cluster.grid(row=row_shift_cluster, column=3, sticky="we")        
        row_shift_cluster += 1  

        self.fig_cluster, self.ax_cluster = plt.subplots(figsize=(5, 4))
        self.fig_cluster.set_facecolor( self.color_code_bcl) #  #EBEBEB
        self.fig_cluster.set_layout_engine(layout="tight")
        self.colorbar_cluster = None
        self.canvas = FigureCanvasTkAgg(self.fig_cluster, master=self.frame_cluster)
        self.canvas.get_tk_widget().grid(row=row_shift_cluster, column=0, columnspan=4)  
        self.canvas.draw()
        row_shift_cluster += 1  

        self.toolbar_cluster_frame = ctk.CTkFrame(self.frame_cluster)        
        self.toolbar_cluster_frame.grid(row=row_shift_cluster, column=0, columnspan=4)
        self.toolbar_cluster = NavigationToolbar2Tk(self.canvas, self.toolbar_cluster_frame)
        self.toolbar_cluster.config(background="#EBEBEB")
        self.toolbar_cluster._message_label.config(background="#EBEBEB")
        for button in self.toolbar_cluster.winfo_children():
            button.config(background="#EBEBEB")        
        self.toolbar_cluster.update()  # Update the toolbar to reflect actions
        row_shift_cluster += 1  

        # ---------------------------------------------    
        # hist2d visualizer 0x1
        # ---------------------------------------------    

        self.frame_hist2d = ctk.CTkFrame(self.root, fg_color=self.color_code_bcl)
        self.frame_hist2d.grid(row=0, column=1, sticky="nsew")
        self.frame_hist2d.grid_rowconfigure((0, 1, 2), weight=0)
        self.frame_hist2d.grid_columnconfigure((0, 1, 2), weight=0)
        row_shift_hist2d = 0

        self.cbox_hist2d_1 = ctk.CTkComboBox(self.frame_hist2d, values=[""], command=self.set_var_hist2d_x)
        self.cbox_hist2d_1.grid(row=row_shift_hist2d, column=0) 
        self.cbox_hist2d_2 = ctk.CTkComboBox(self.frame_hist2d, values=[""], command=self.set_var_hist2d_y)
        self.cbox_hist2d_2.grid(row=row_shift_hist2d, column=1) 
        self.bt_hist2d_plot = ctk.CTkButton(self.frame_hist2d, text="Plot", command=self.show_hist2d)
        self.bt_hist2d_plot.grid(row=row_shift_hist2d, column=2) 
        row_shift_hist2d += 1  

        self.fig_hist2d, self.ax_hist2d = plt.subplots(figsize=(5, 4))
        self.fig_hist2d.set_facecolor( self.color_code_bcl) #  #EBEBEB 
        self.fig_hist2d.set_layout_engine(layout="tight")        
        self.colorbar_hist2d = None
        self.canvas_hist2d = FigureCanvasTkAgg(self.fig_hist2d, master=self.frame_hist2d)
        self.canvas_hist2d.get_tk_widget().grid(row=row_shift_hist2d, column=0, columnspan=3)  
        self.canvas_hist2d.draw()  
        row_shift_hist2d += 1  

        self.toolbar_hist2d_frame = ctk.CTkFrame(self.frame_hist2d)        
        self.toolbar_hist2d_frame.grid(row=row_shift_hist2d, column=0, columnspan=3)
        self.toolbar_hist2d = NavigationToolbar2Tk(self.canvas_hist2d, self.toolbar_hist2d_frame)
        self.toolbar_hist2d.config(background="#EBEBEB")
        self.toolbar_hist2d._message_label.config(background="#EBEBEB")
        for button in self.toolbar_hist2d.winfo_children():
            button.config(background="#EBEBEB")        
        self.toolbar_hist2d.update()  # Update the toolbar to reflect actions
        row_shift_hist2d += 1  

        # ---------------------------------------------    
        # clusters visualizer 1x1
        # ---------------------------------------------    

        self.frame_clusters = ctk.CTkFrame(self.root, fg_color=self.color_code_bcl)
        self.frame_clusters.grid(row=1, column=1, sticky="nsew")
        self.frame_clusters.grid_rowconfigure((0, 1, 2), weight=0)
        self.frame_clusters.grid_columnconfigure((0, 1, 2), weight=0)
        row_shift_clusters = 0

        self.bt_prev_clusters = ctk.CTkButton(self.frame_clusters, text="<", command=self.show_prev_clusters)
        self.bt_prev_clusters.grid(row=row_shift_clusters, column=0,  sticky="e")  
        self.lbl_clusters_num = ctk.CTkLabel(self.frame_clusters, text="-")
        self.lbl_clusters_num.grid(row=row_shift_clusters, column=1)    
        self.bt_next_clusters = ctk.CTkButton(self.frame_clusters, text=">", command=self.show_next_clusters)
        self.bt_next_clusters.grid(row=row_shift_clusters, column=2,  sticky="w")  
        row_shift_clusters += 1      
        
        self.fig_clusters, self.ax_clusters = plt.subplots(figsize=(5, 4))
        self.fig_clusters.set_facecolor( self.color_code_bcl) #  #EBEBEB 
        self.fig_clusters.set_layout_engine(layout="tight")                
        self.colorbar_clusters = None
        self.canvas_clusters = FigureCanvasTkAgg(self.fig_clusters, master=self.frame_clusters)
        self.canvas_clusters.get_tk_widget().grid(row=row_shift_clusters, column=0, columnspan=3)  
        self.canvas_clusters.draw()  
        row_shift_clusters += 1      

        self.toolbar_clusters_frame = ctk.CTkFrame(self.frame_clusters)        
        self.toolbar_clusters_frame.grid(row=row_shift_clusters, column=0,  columnspan=3)
        self.toolbar_clusters = NavigationToolbar2Tk(self.canvas_clusters, self.toolbar_clusters_frame)
        self.toolbar_clusters.config(background="#EBEBEB")
        self.toolbar_clusters._message_label.config(background="#EBEBEB")
        for button in self.toolbar_clusters.winfo_children():
            button.config(background="#EBEBEB")        
        self.toolbar_clusters.update()  # Update the toolbar to reflect actions
        row_shift_clusters += 1      


        # ---------------------------------------------
        # options 2x0-1
        # ---------------------------------------------
        
        self.frame_opt = ctk.CTkFrame(self.root, fg_color=self.color_code_bcl)
        self.frame_opt.grid(row=0, column=2, rowspan=2, sticky="nsew")
        self.frame_opt.grid_rowconfigure((0, 1, 2, 3), weight=0)
        self.frame_opt.grid_columnconfigure((0), weight=0)



        self.frame_opt_file = ctk.CTkFrame(self.frame_opt, fg_color=self.color_code_bcl_fr)
        self.frame_opt_file.grid(row=0, column=0, sticky="ew")
        # self.frame_opt_file.grid_rowconfigure((0, 1, 2), weight=0)
        self.frame_opt_file.grid_columnconfigure((0, 1, 2), weight=0)
        row_shift_opt_file = 0

        self.lbl_sel_file = ctk.CTkLabel(self.frame_opt_file, text=" ", font=('Helvetica', 16, 'bold'))
        self.lbl_sel_file.grid(row=row_shift_opt_file, column=0, sticky="w")   
        row_shift_opt_file += 1        

        self.lbl_select_load_file= ctk.CTkLabel(self.frame_opt_file, text="Path to file for processing:\t")
        self.lbl_select_load_file.grid(row=row_shift_opt_file, column=0, sticky="w") 
        row_shift_opt_file += 1

        self.en_file = ctk.CTkEntry(self.frame_opt_file, placeholder_text = f"path to file")
        self.en_file.grid(row=row_shift_opt_file, column=0, sticky="we", columnspan=2)  
        self.bt_hist2d_plot = ctk.CTkButton(self.frame_opt_file, text="Select file", command=self.select_load_file)
        self.bt_hist2d_plot.grid(row=row_shift_opt_file, column=2, sticky="e", padx=20, pady=2) 
        row_shift_opt_file += 1        

        self.lbl_cluster_max = ctk.CTkLabel(self.frame_opt_file, text="Clusters count for loading:")
        self.lbl_cluster_max.grid(row=row_shift_opt_file, column=0, sticky="w")  
        self.en_cluster_max = ctk.CTkEntry(self.frame_opt_file, placeholder_text = f"{self.cluster_count_max}")
        self.en_cluster_max.grid(row=row_shift_opt_file, column=1, sticky="e")  
        row_shift_opt_file += 1

        self.lbl_clist_ext_var= ctk.CTkLabel(self.frame_opt_file, text="Switch tto include extension of clist:\t")
        self.lbl_clist_ext_var.grid(row=row_shift_opt_file, column=0, sticky="w")         
        self.swch_clist_ext_var = ctk.CTkSwitch(self.frame_opt_file, text="", state="enabled",
                                                command=self.switch_to_clist_ext_var)
        self.swch_clist_ext_var.grid(row=row_shift_opt_file, column=2, sticky="e")  
        row_shift_opt_file += 1

        # self.lbl_cluster_idx_start = ctk.CTkLabel(self.frame_opt_file, text="Index of first cluster in clist:")
        # self.lbl_cluster_idx_start.grid(row=row_shift_opt_file, column=0, sticky="w")  
        # self.en_cluster_idx_start = ctk.CTkEntry(self.frame_opt_file, placeholder_text = f"0")
        # self.en_cluster_idx_start.grid(row=row_shift_opt_file, column=1, sticky="e")  
        # row_shift_opt_file += 1

        self.bt_load_file = ctk.CTkButton(self.frame_opt_file, text="Load file", command=self.load_file)
        self.bt_load_file.grid(row=row_shift_opt_file, column=0, columnspan=3, sticky="ew", pady=2) 
        row_shift_opt_file += 1       


        self.lbl_select_save_clist_file= ctk.CTkLabel(self.frame_opt_file, text="Save data/clist into file:\t")
        self.lbl_select_save_clist_file.grid(row=row_shift_opt_file, column=0, sticky="w") 
        row_shift_opt_file += 1

        self.en_save_clist_file = ctk.CTkEntry(self.frame_opt_file, placeholder_text = f"path to file for clists")
        self.en_save_clist_file.grid(row=row_shift_opt_file, column=0, sticky="we", columnspan=2)  
        self.bt_select_clist_file = ctk.CTkButton(self.frame_opt_file, text="Select file", 
                                    command=self.select_clist_file_save)
        self.bt_select_clist_file.grid(row=row_shift_opt_file, column=2, sticky="e", padx=20, pady=2) 
        row_shift_opt_file += 1        

        self.bt_save_clist_file = ctk.CTkButton(self.frame_opt_file, text="Save clists", 
                                                    command=self.save_clist)
        self.bt_save_clist_file.grid(row=row_shift_opt_file, column=0, columnspan=3, sticky="ew") 
        row_shift_opt_file += 1       


        # self.frame_opt_filter = ctk.CTkFrame(self.frame_opt, fg_color=self.color_code_bcl_fr)
        # self.frame_opt_filter.grid(row=1, column=0, columnspan=3, sticky="ew")
        # # self.frame_opt_filter.grid_rowconfigure((0, 1, 2), weight=0)
        # self.frame_opt_filter.grid_columnconfigure((0, 1, 2), weight=0)
        # row_shift_opt_filter = 0

        self.lbl_sel_file = ctk.CTkLabel(self.frame_opt_file, text=" ", font=('Helvetica', 14, 'bold'))
        self.lbl_sel_file.grid(row=row_shift_opt_file, column=0, sticky="w")           
        row_shift_opt_file += 1       

        self.scrollable_frame = ctk.CTkScrollableFrame(self.frame_opt_file, label_text="Filters")
        self.scrollable_frame.grid(row=row_shift_opt_file, column=0, columnspan=3, sticky="nsew")
        # self.scrollable_frame.grid_columnconfigure(0, weight=1)
        row_shift_opt_file += 1      

        self.bt_filter = ctk.CTkButton(self.frame_opt_file, text="Apply filters", command=self.filter_data)
        self.bt_filter.grid(row=row_shift_opt_file, column=0, columnspan=3, sticky="ew")  
        row_shift_opt_file += 1

        self.lbl_filter_out= ctk.CTkLabel(self.frame_opt_file, text="Switch to filtered out data:\t")
        self.lbl_filter_out.grid(row=row_shift_opt_file, column=0, sticky="w")         
        self.swch_filter_out = ctk.CTkSwitch(self.frame_opt_file, text="", state="disabled",
                                                command=self.switch_to_filetered_data)
        self.swch_filter_out.grid(row=row_shift_opt_file, column=2, sticky="e")  
        row_shift_opt_file += 1
       

        self.lbl_select_save_filter_file= ctk.CTkLabel(self.frame_opt_file, text="Save filter into INI file:\t")
        self.lbl_select_save_filter_file.grid(row=row_shift_opt_file, column=0, sticky="w") 
        row_shift_opt_file += 1

        self.en_save_filter_file = ctk.CTkEntry(self.frame_opt_file, placeholder_text = f"path to file for filters")
        self.en_save_filter_file.grid(row=row_shift_opt_file, column=0, sticky="we", columnspan=2)  
        self.bt_select_filter_file = ctk.CTkButton(self.frame_opt_file, text="Select file", 
                                    command=self.select_filter_file)
        self.bt_select_filter_file.grid(row=row_shift_opt_file, column=2, sticky="e", padx=20, pady=2) 
        row_shift_opt_file += 1        

        self.bt_save_filter_file = ctk.CTkButton(self.frame_opt_file, text="Save filters", 
                                                    command=self.save_filter_to_ini)
        self.bt_save_filter_file.grid(row=row_shift_opt_file, column=0, columnspan=3, sticky="ew") 
        row_shift_opt_file += 1       

        # self.frame_opt_stat = ctk.CTkFrame(self.frame_opt, fg_color=self.color_code_bcl_fr)
        # self.frame_opt_stat.grid(row=2, column=0, sticky="ew")
        # # self.frame_opt_stat.grid_rowconfigure((0, 1, 2), weight=0)
        # self.frame_opt_stat.grid_columnconfigure((0, 1, 2), weight=0)
        # row_shift_opt_file = 0

        self.lbl_sel_file = ctk.CTkLabel(self.frame_opt_file, text=" ", font=('Helvetica', 14, 'bold'))
        self.lbl_sel_file.grid(row=row_shift_opt_file, column=0, sticky="w")           
        row_shift_opt_file += 1     

        self.lbl_clusters_cnt_ok = ctk.CTkLabel(self.frame_opt_file, text="Count of OK clusters:\t")
        self.lbl_clusters_cnt_ok.grid(row=row_shift_opt_file, column=0, sticky="w")          
        self.lbl_clusters_cnt_ok = ctk.CTkLabel(self.frame_opt_file, text="-")
        self.lbl_clusters_cnt_ok.grid(row=row_shift_opt_file, column=2, sticky="w") 
        row_shift_opt_file += 1

        self.lbl_clusters_cnt_out = ctk.CTkLabel(self.frame_opt_file, text="Count of filtered out clusters:\t")
        self.lbl_clusters_cnt_out.grid(row=row_shift_opt_file, column=0, sticky="w")          
        self.lbl_clusters_cnt_out = ctk.CTkLabel(self.frame_opt_file, text="-")
        self.lbl_clusters_cnt_out.grid(row=row_shift_opt_file, column=2, sticky="w") 
        row_shift_opt_file += 1


        # self.frame_opt_others = ctk.CTkFrame(self.frame_opt, fg_color=self.color_code_bcl_fr)
        # self.frame_opt_others.grid(row=3, column=0, sticky="ew")
        # # self.frame_opt_others.grid_rowconfigure((0, 1, 2), weight=0)
        # self.frame_opt_others.grid_columnconfigure((0, 1, 2), weight=0)
        # row_shift_opt_others = 0

        self.lbl_sel_file = ctk.CTkLabel(self.frame_opt_file, text=" ", font=('Helvetica', 14, 'bold'))
        self.lbl_sel_file.grid(row=row_shift_opt_file, column=0, sticky="w")           
        row_shift_opt_file += 1     

        self.lbl_reset= ctk.CTkLabel(self.frame_opt_file, text="Reset to original data:\t")
        self.lbl_reset.grid(row=row_shift_opt_file, column=0, sticky="w") 
        self.bt_reset = ctk.CTkButton(self.frame_opt_file, text="Reset", command=self.reset)
        self.bt_reset.grid(row=row_shift_opt_file, column=2, sticky="e")   
        row_shift_opt_file += 1


        # ---------------------------------------------

    def print_info(self):
        print(f"[INFO] Cluster Visualizer {self.version} {self.date}")

    def select_load_file(self):

        initial_dir = self.file_in_path
        if not  self.file_in_path:
            initial_dir =  current_dir

        filetypes = (
            ('clist files', '*.clist'),
            ('All files', '*.*')
        )

        self.file_in_path = fd.askopenfilename(
            title='Open a file',
            initialdir=initial_dir,
            filetypes=filetypes)

        self.en_file.insert(1,self.file_in_path)

        self.load_file()


    """select file for processing"""
    def load_file(self):

        if self.en_file.get():
            self.file_in_path = self.en_file.get()
            print(f"[INFO] File: {self.file_in_path}")

        # test
        # self.file_in_path = "./devel/in/data.clist"

        self.open_read_file()

        var_keys = [var_key for var_key in self.clist.var_keys if var_key != "ClusterPixels"]

        self.cbox_hist1d.configure(values=var_keys)

        for i, var_key in enumerate(var_keys):     
            lbl_treshold_max = ctk.CTkLabel(master=self.scrollable_frame, text=var_key)
            lbl_treshold_max.grid(row=i, column=1) 

            en_threshold_min = ctk.CTkEntry(master=self.scrollable_frame, placeholder_text = "minimum")
            en_threshold_min.grid(row=i, column=2)

            en_threshold_max = ctk.CTkEntry(master=self.scrollable_frame, placeholder_text = "maximum")
            en_threshold_max.grid(row=i, column=3)

            self.filter_entries.append([var_key, en_threshold_min, en_threshold_max])

        self.cbox_hist2d_1.configure(values=var_keys)
        self.cbox_hist2d_2.configure(values=var_keys)

        self.update_show()
        self.update_stat()

    """open found files and load them into np"""
    def open_read_file(self):
        if self.file_in_path:
            print(f"[INFO] Opening and reading file: {self.file_in_path}.")

            try:
                self.cluster_count_max = int(self.en_cluster_max.get())
            except:
                pass

            try:
                self.clist_ok = Clist()
                self.clist_ok.load(self.file_in_path,nrows=self.cluster_count_max)
                print("===================================")
                self.clist_ok.print()
                print("===================================")

                if self.clist_use_extension:
                    self.clist_ok.extend_varaibles()

                self.clist = self.clist_ok

                self.clist_out = copy.deepcopy(self.clist_ok)
                self.clist_out.data = pd.DataFrame()

                self.clist_orig = copy.deepcopy(self.clist_ok)
            except:
                print("[ERROR] Can not open clist:", self.file_in_path)

    def reset(self):
        if self.clist is not None:
            self.clist_ok = copy.deepcopy(self.clist_orig)

            self.clist_out = copy.deepcopy(self.clist_ok)
            self.clist_out.data = pd.DataFrame()

            self.clist = self.clist_ok

            if not self.show_clist_ok:
                self.swch_filter_out.deselect()
                self.show_clist_ok = True

            for filter_entry in self.filter_entries:
                filter_entry[1].delete(0,len(filter_entry[1].get()))
                filter_entry[2].delete(0,len(filter_entry[2].get()))

            self.cluster_id_curr = 1
            self.clusters_curr_start = 0
            self.clusters_batch_curr = 1

            self.filters_curr.clear()
            self.file_filter_ini = None

            self.update_show()
            self.update_stat()

    def update_show(self):
        self.show_cluster(self.cluster_id_curr)
        self.show_hist1d("")
        self.show_clusters()
        self.show_hist2d()

    def update_stat(self):
        self.clusters_count_ok = len(self.clist_ok.data)
        self.clusters_count_out = len(self.clist_out.data)

        clusters_cout_all = self.clusters_count_ok + self.clusters_count_out
        if clusters_cout_all == 0:
            clusters_cout_all = 1

        self.lbl_clusters_cnt_ok.configure(text=f"{self.clusters_count_ok}\t{100*self.clusters_count_ok/clusters_cout_all:.2f}%")
        self.lbl_clusters_cnt_out.configure(text=f"{self.clusters_count_out}\t{100*self.clusters_count_out/clusters_cout_all:.2f}%")


    def switch_hist1d_log_x(self):
        self.hist1d_log_x = not self.hist1d_log_x
        self.show_hist1d("")

    def switch_hist1d_log_y(self):
        self.hist1d_log_y = not self.hist1d_log_y
        self.show_hist1d("")

    def switch_to_clist_ext_var(self):
        self.clist_use_extension = not self.clist_use_extension
        print(f"[INFO] Switched to {self.clist_use_extension} to use clist varaibles extension.")

    def switch_to_filetered_data(self):
        if self.clist_out is not None and not self.clist_out.data.empty:
            if self.show_clist_ok:
                self.show_clist_ok = False
                self.clist = self.clist_out
                self.update_show()
            else:
                self.show_clist_ok = True
                self.clist = self.clist_ok
                self.update_show()

    def switch_to_keep_same_hist1d_bin(self):
        if self.clist_out is not None and not self.clist_out.data.empty:
            self.hist1d_keep_same_bins = not self.hist1d_keep_same_bins
            self.show_hist1d("")

    """show one cluster based on the idx"""
    def show_cluster(self, cluster_idx):
        if self.clist is None or self.clist.data.empty:
            print("[ERROR] Clist not loaded or empty.")
            return

        if cluster_idx >= len(self.clist.data):
            cluster_idx = len(self.clist.data) - 1

        try:
            print(f"[INFO] Showing cluster at idx: {cluster_idx}")

            self.clear_image_axes(self.fig_cluster, self.ax_cluster, self.colorbar_cluster)

            cluster = self.clist.get_cluster(cluster_idx=cluster_idx)
            self.cluster_curr = cluster
            self.cluster_id_curr = cluster_idx

            hist, self.colorbar_cluster = cluster.plot(2, self.fig_cluster,  self.ax_cluster, show_plot=False)

            self.lbl_cluster_num.configure(text=str(cluster_idx))

            self.ax_cluster.set_xlabel("X [px]")
            self.ax_cluster.set_xlabel("Y [px]")

            self.canvas.draw()

            self.cluster_par_list = self.cluster_params_as_text_list()
            self.cbox_cluster.configure(values=self.cluster_par_list)
            self.cbox_cluster.set(self.cluster_par_list[self.cluster_par_curr_idx])
        except Exception as e:
            print(f"[ERROR] Failed to show cluster:\t{cluster_idx}: {e}.")

    def cluster_params_as_text_list(self):
        if self.clist is not None and not self.clist.data.empty:

            par_text_list = []
            gap = "  =  " 

            for idx, num in enumerate(self.clist.data.iloc[self.cluster_id_curr]):
                var_key = self.clist.var_keys[idx]
                var_unit = self.clist.var_units[idx]

                if var_key == "ClusterPixels":
                    continue
                text = var_key + gap + str(num) + " " + var_unit
                par_text_list.append(text)

            return par_text_list
        else:
            return [""]

    def set_cluster_par_curr_idx(self, text):
        position = 4
        if text in self.cluster_par_list:
            position = self.cluster_par_list.index(text)        

        self.cluster_par_curr_idx = position

    def show_prev_cluster(self):
        if self.clist is not None:
            if self.cluster_id_curr > 0:
                self.cluster_id_curr -= 1
                self.show_cluster(self.cluster_id_curr)  
            elif self.cluster_id_curr == 0:
                self.cluster_id_curr = len(self.clist.data)-1
                self.show_cluster(self.cluster_id_curr)  

    def show_next_cluster(self):
        if self.clist is not None:
            if self.cluster_id_curr < len(self.clist.data)-1:
                self.cluster_id_curr += 1
                self.show_cluster(self.cluster_id_curr)  
            else:  
                self.cluster_id_curr = 1
                self.show_cluster(self.cluster_id_curr)  

    def show_clusters(self):
        if self.clist is None or self.clist.data.empty:
            print("[ERROR] Clist not loaded or empty.")
            return     
        try:
            self.ax_clusters.clear()
            for ax_curr in self.fig_clusters.axes:
                ax_curr.clear()
                if ax_curr != self.ax_clusters:
                    ax_curr.remove()      
            print(f"[INFO] Showing {self.clusters_batch_curr} batch of {self.clusters_count_show} clusters from {self.clusters_curr_start}.")
            self.colorbar_clusters = self.clist.plot_clusters(fig=self.fig_clusters, ax=self.ax_clusters, do_show=False,
                                    cluster_count=self.clusters_count_show, idx_start=self.clusters_curr_start)
            self.ax_clusters.set_xlabel("X [px]")
            self.ax_clusters.set_xlabel("Y [px]")
            self.colorbar_clusters.set_label(self.colorbar_cluster.ax.get_ylabel())        
            self.lbl_clusters_num.configure(text=str(self.clusters_batch_curr))        
            print(f"[INFO] Showing {self.clusters_batch_curr} batch of clusters finished.")        
            self.canvas_clusters.draw()
        except:
            print(f"[ERROR] Showing {self.clusters_batch_curr} batch of {self.clusters_count_show} clusters from {self.clusters_curr_start} failed.")


    def show_prev_clusters(self):
        if self.clist is not None:
            if self.clusters_curr_start - self.clusters_count_show > 0:
                self.clusters_curr_start -= self.clusters_count_show
                self.clusters_batch_curr -= 1 
                self.show_clusters()     
            else:
                self.clusters_batch_curr = int(len(self.clist.data)/self.clusters_count_show)
                self.clusters_curr_start = self.clusters_count_show*self.clusters_batch_curr
                self.show_clusters()     

    def show_next_clusters(self):
        if self.clist is not None:
            if self.clusters_curr_start + self.clusters_count_show < len(self.clist.data):
                self.clusters_curr_start += self.clusters_count_show
                self.clusters_batch_curr += 1                 
                self.show_clusters()      
            else:
                self.clusters_curr_start = 0
                self.clusters_batch_curr = 1
                self.show_clusters()                      


    """clears image z axis to prevent over plotting"""
    def clear_image_axes(self, fig, ax, colorbar):
        if colorbar is not None:
            colorbar.remove()
            colorbar = None
        for ax_curr in fig.axes:
            ax_curr.clear()
            if ax_curr != ax:
                ax_curr.remove()


    def show_hist1d(self, var_key):
        if self.clist is None or self.clist.data.empty:
            print("[ERROR] Clist not loaded or empty.")
            return

        if not len(var_key):
            var_key = self.hist1d_curr_var

        self.ax_hist1d.clear()

        xmin=None
        xmax=None
        nbin=100

        if self.hist1d_keep_same_bins and var_key in self.hist1d_history:
            xmin=self.hist1d_history[var_key][0]
            xmax=self.hist1d_history[var_key][1]
            nbin=self.hist1d_history[var_key][2]

        hist1d_1 = self.clist.plot(var_key, ax=self.ax_hist1d, do_show=False, 
                        do_log_x = self.hist1d_log_x, do_log_y = self.hist1d_log_y,
                        xmin=xmin, xmax=xmax, nbin=nbin )

        if self.hist1d_keep_same_bins and var_key not in self.hist1d_history:
            self.hist1d_history[var_key] = [hist1d_1.xmin, hist1d_1.xmax, hist1d_1.nbin]

        self.canvas_hist1d.draw()
        self.ax_hist1d.set_title("")

        self.hist1d_curr_var = var_key

    def set_var_hist2d_x(self, var):
        if var:
            self.var_hist2d_x = var

    def set_var_hist2d_y(self, var):
        if var:
            self.var_hist2d_y = var

    def show_hist2d(self):
        if self.clist is None or self.clist.data.empty:
            print("[ERROR] Clist not loaded or empty.")
            return

        self.clear_image_axes(self.fig_hist2d, self.ax_hist2d, self.colorbar_hist2d)

        hist2d, self.colorbar_hist2d =  self.clist.plot_hist2d(self.var_hist2d_x, self.var_hist2d_y, 
                                                                fig=self.fig_hist2d, ax=self.ax_hist2d, 
                                                                do_show=False)

        self.canvas_hist2d.draw()             


    def filter_data(self):
        if self.clist is None or self.clist.data.empty:
            print("[ERROR] Clist not loaded or empty.")
            return

        self.filters_curr.clear()

        for filter_entry in self.filter_entries:

            var_key = filter_entry[0]
            entry_min = filter_entry[1]
            entry_max = filter_entry[2]

            if entry_min.get() or entry_max.get() :

                filter_min = -1e100
                filter_max = 1e100

                try:
                    filter_min = float(entry_min.get())
                except: pass
                try:
                    filter_max = float(entry_max.get())
                except: pass

                clist_data_filter_out = None

                print(f"[INFO] Using filter: {var_key} from {filter_min} ro {filter_max}")
                self.clist_ok.data, clist_data_filter_out =  self.clist_ok.filter_data_frame( var_key, filter_min, filter_max, keep_data = True,
                                                                                    get_out_data = True)

                if clist_data_filter_out is not None and not clist_data_filter_out.empty:
                    self.swch_filter_out.configure(state="normal")
                    self.clist_out.data = pd.concat([self.clist_out.data, clist_data_filter_out] , 
                                                    ignore_index=True)

                self.filters_curr.append([var_key ,filter_min, filter_max])

        if self.show_clist_ok:
            self.clist = self.clist_ok
        else:
            self.clist = self.clist_out

        self.update_show()
        self.update_stat()

    def select_filter_file(self):

        initial_dir = self.file_filter_ini_path
        if not  self.file_in_path:
            initial_dir =  current_dir

        filetypes = (
            ('ini files', '*.ini'),
            ('All files', '*.*')
        )

        self.file_filter_ini = fd.asksaveasfile(
            title='Open a file',
            initialdir=initial_dir,
            filetypes=filetypes)
        
        if self.file_filter_ini is None: 
            print("[ERROR] Fail to save filter file.")
            return

        self.file_filter_ini_path = self.file_filter_ini.name        

        self.en_save_filter_file.insert(1, self.file_filter_ini_path)

    def save_filter_to_ini(self):
        
        self.file_filter_ini_path = self.en_save_filter_file.get()

        if not self.filters_curr:
            print(f"[INFO] No filters applied to be saved into file.")

        if  not self.file_filter_ini_path:
            print("[ERROR] Fail to save filter into ini file. No path given.")
            return

        try:
            if self.file_filter_ini is None:
                self.file_filter_ini = open(self.file_filter_ini_path, "w")

            for filter_curr in self.filters_curr:
                var_key = filter_curr[0]
                filter_min = filter_curr[1]
                filter_max = filter_curr[2]

                self.file_filter_ini.write(f"[{var_key}]\n")
                self.file_filter_ini.write(f"Range = {filter_min},{filter_max}\n")

            self.file_filter_ini.close()    
            self.file_filter_ini = None
        except:
            print(f"[ERROR] Fail to save filter in ini file: {self.file_filter_ini_path}.")
            return

        print(f"[INFO] Filter saved into file {self.file_filter_ini_path}.")


    def select_clist_file_save(self):

        initial_dir = self.file_clist_path
        if not  self.file_in_path:
            initial_dir =  current_dir

        filetypes = (
            ('ini files', '*.clist'),
            ('All files', '*.*')
        )

        self.file_clist = fd.asksaveasfile(
            title='Open a file',
            initialdir=initial_dir,
            filetypes=filetypes)
        
        if self.file_clist is None: 
            print("[ERROR] Fail to save clist file.")
            return

        self.file_clist_path = self.file_clist.name        

        self.en_save_clist_file.insert(1, self.file_clist_path)

    def save_clist(self):
        
        self.file_clist_path = self.en_save_clist_file.get()

        if self.clist is None:
            print(f"[INFO] No clists applied to be saved into file.")

        if  not self.file_clist_path:
            print("[ERROR] Fail to save clist into ini file. No path given.")
            return

        if self.file_clist:
            self.file_clist.close()
            self.file_clist = None

        try:
            self.clist.export(self.file_clist_path)
        except:
            print(f"[ERROR] Fail to save clist in ini file: {self.file_clist_path}.")
            return

        print(f"[INFO] clist saved into file {self.file_clist_path}.")

if __name__ == "__main__":
    root = ctk.CTk()
    app = ClusterVisualuzerGUI(root)
    root.mainloop()
