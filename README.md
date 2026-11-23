## Overview
The Sonic Radiation Belt Environment Toolkit (SoRBET) is a STRAUSS-powered sonification 
library whose aims are to make the amazing work of STRAUSS and the intangible world of 
space physics more accessible to non-specialist of all varieties, but especially publics.

### Credit and Thanks
None of this would have been possible without the Sonic Intangibles team, who taught me the basic principles of sonification in the first place, but especially Chris Harrison and Rose Shepherd for introducing me to STRAUSS and teaching me how to use it. A lot of the fundamentals backends of SoRBET are adapted from a tutorial that Rose herself made, which helped STRAUSS to finally click with me!

Additionally, a lot of the design choices and ethos of SoRBET were in no small part due to Ollie and Annabelle, two high school students and Cramlington Learning Village. These two were the first to test, feed back on and create with SoRBET and their work helped to shape the development of SoRBET into what it is now. 

### Structure and usage
The main sonification tools within SoRBET are the following:
1) The most basic sonification tools, which produce sounds with one varying property (audio graphs) are created using PLUM (Principal Librarys for Univariate Mappings). Great for those looking to explore sonification for the first time
2) For more creative control, and to make more compound sonifications, there's ManGOE (Man Generation of Objects and Events) that allows data to be assigned to maps and fed into the sonification function along with map limits.

Future releases will contain the Spectral Libraries for Object and Events (SLOE) as well as the data loading capabilities for obtaining NASA data
