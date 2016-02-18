import numpy as np
import quakelib
import re, sys, collections

# Change this to match your computer/file system
WORKING_DIR = '/Users/kasey/VQModels/'
ASEISMIC_CUT = 0.11
STRESS_DROP = 0.5
SAVE_FILE_GEO = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Geometry.dat'
SAVE_FILE_FRIC = WORKING_DIR+'UCERF3/UCERF3_EQSim_AseismicCut_'+str(ASEISMIC_CUT)+'_ReFaulted_Friction.dat'

# Original UCERF 3 model
UCERF3 = WORKING_DIR+'UCERF3/UCERF3_EQSIM_FM3_1_ZENGBB_Geometry.dat'
UCERF3_fric = WORKING_DIR+'UCERF3/UCERF3_EQSIM_Friction.dat'
model = quakelib.ModelWorld()
model.read_files_eqsim(UCERF3, "", UCERF3_fric, "none")
#model.read_file_ascii(UCERF3)
#model.read_file_hdf5(UCERF3)
fault_ids = model.getFaultIDs()

# Creating a new model world for the modified faults
new_model = quakelib.ModelWorld()

uniq_faults = {}
uniq_faults_combined = {}

print("------Read "+str(len(model.getSectionIDs()))+" Sections-----")
print("------     belonging to "+str(len(fault_ids))+" Faults-----")

# Removing all instances of ..._Subsection_1.. etc
# Removing all instances of ..._2011_CFM
# Upon visual inspection, this tag means a new section was added 
#   to extend an old one, even though both are the same fault.

REGEX_strings = ['_Subsection_(\d)+', '_2011','_CFM', '_Extension', '_extension',
                '_alt_1', '_alt1', '_connector', '_Keough_Hot_Springs','_No$', '_So$',
                '_North$','_South$', '_north$','_south$', '_East$', '_West$', 
                '_San_Fernando$', '_Offshore$','_Onshore$']



# The following faults have multiply named sections containing the following key words, 
#   its easier to match these than cut out each instance of the variant names.
special_faults = ['Calaveras','Contra_Costa','Death_Valley','Elsinore','Garlock',
                    'Kern_Canyon','San_Andreas','San_Jacinto']
special_fault_ids = [602,626,246,299,341,544,295,101]
assert(len(special_fault_ids)==len(special_faults))

# Input the special faults as the first entries in the combined uniq_faults dictionary
for i, name in enumerate(special_faults):
    uniq_faults_combined[name] = special_fault_ids[i]



# Loop once over sections to determine the unique fault names and IDs
for sec_id in sorted(model.getSectionIDs()):
    sec_name = model.section(sec_id).name()
    sec_fault_id = model.section(sec_id).fault_id()
    
    trimmed_name = sec_name
    for REGEX in REGEX_strings:
        trimmed_name = re.sub(REGEX, '', trimmed_name)
    
    uniq_faults[trimmed_name] = sec_fault_id
    
print("------Parsed "+str(len(uniq_faults.keys()))+" Uniquely Named Faults-----")
    
# Print the semi-final faults
#for key, val in uniq_faults.iteritems():
#    print('{}\t{}'.format(val, key))
    
    
# Loop over the sections again to reset the fault IDs to whichever unique fault matches
for sec_id in sorted(model.getSectionIDs()):
    sec_name = model.section(sec_id).name()
    
    trimmed_name = sec_name
    for REGEX in REGEX_strings:
        trimmed_name = re.sub(REGEX, '', trimmed_name)
    
    # ===== These get set if the trimmed name contains a special fault name.
    #           If no match, then it is assumed to be a unique fault.
    new_fault_id = None
    new_fault_name = None
    
    # Try to find a special fault name that matches
    for i, spec_fault_name in enumerate(special_faults):
        if trimmed_name.find(spec_fault_name) >= 0:
            new_fault_id = special_fault_ids[i]
            new_fault_name = spec_fault_name
            break
    
    # If no match to special faults, then process it as a uniquely named fault.
    # Try to grab an already-processed fault_id of a previous fault with the 
    #     same unique fault name.
    if new_fault_id is None:
        new_fault_name = trimmed_name
        try:
            new_fault_id = uniq_faults_combined[trimmed_name]
            
        except KeyError:
            new_fault_id = model.section(sec_id).fault_id()
            uniq_faults_combined[new_fault_name] = new_fault_id
            
    # Now that the fault has been matched to a unique one, reset fault_id
    if new_fault_id is None:
        raise "Error: Did not match any unique faults."
    else:
        model.section(sec_id).set_fault_id(new_fault_id)
    

# Order the faults alphabetically
ordered_uniq_faults = collections.OrderedDict(sorted(uniq_faults_combined.items()))

# Print the final faults
#for key, val in ordered_uniq_faults.iteritems():
#    print('{}\t{}'.format(val, key))
 
print("=== Combined into "+str(len(ordered_uniq_faults.keys()))+" Unique Faults ====")



# ================ Apply a lower limit to the aseismic slip ===============
for ele_id in model.getElementIDs():
    this_element = model.element(ele_id)
    if this_element.aseismic() < ASEISMIC_CUT:
        this_element.set_aseismic(0.0)
        

 
# ============ OUTPUT THE MODIFIED MODEL ==============
#new_model.insert(model)
model.write_files_eqsim(SAVE_FILE_GEO, "", SAVE_FILE_FRIC)
print("New model files written: {}, {}".format(SAVE_FILE_GEO,SAVE_FILE_FRIC))




'''
new_model.insert(model)
new_model.create_faults('none')
new_model.compute_stress_drops(model.stressDropFactor())
new_model.setStressDropFactor(model.stressDropFactor())
new_model.write_file_ascii(new_file_txt)

print("New model file written: {}".format(new_file_txt))
'''

    