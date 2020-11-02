## iSnap Examples Documentation
For the behavior examples in iSnap project, there are 2 major JS files - renderGifs.js and behavior.js - and one css file. Some of the functionality is added to proactive-example-display.js file as well. Below is the description and some relevant details for the files: 

  - **isnap/hints/proactive-example-display.js**
    
      -- The functionality in this file creates a basic skeleton for the gallery to display the gifs. Whenever the "show examples" button is clicked, the *setBehaviorModal* functions is executed which creates the above HTML skeleton and adds the necessary js (including the slick library) and script files to the html. 
      
  - **isnap/behavior/renderGifs.js**
     This file contains the data in the variable "name_dict" which is used to create and render all the gifs dynamically. The file also handles the scenario for searching a gif or clearing the search results. The function *searchForFeedBackEx* is executed whenever the search button is clicked. The function searches for the entered text (in the search field) and re-renders the HTML gif examples according to the matching results. *extractAndRenderTags* function extracts the tags from the "name_dict" and renders them. It handles the clicks on the tags as well.
  
  - **isnap/behavior/behavior.js**

      -- This file contains the logic for the transition from gallery to the overlay (small window on the right corner) and vice-versa. The function *addClickToGifs* handles the tranisitions for both - gallery to overlay and overlay to gallery. The two functions *galleryToOverlayTransitionFunction* and *overlayToGalleryTransitionFunctions* handle the transitions. Whenever the transition occurs from gallery to overlay, the unnecessary HTML elements are either removed or hidden. Similarly, when the opposite transition occurs i.e. from overlay to gallery, the required elements are added again or shown respectively.
