from calibrate.d_to_p_prep import D_to_P_prep

prepper = D_to_P_prep(200)
prepper.merge_d_to_p(["output\Final_averaged_data\DtoP_13.csv",
                      "output\Final_averaged_data\DtoP_24.csv",
                      "output\Final_averaged_data\DtoP_33.csv",
                      "output\Final_averaged_data\DtoP_43.csv",], "wheelchair_DtoP")