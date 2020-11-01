## iSnap feature extension
For the iSnap project (frontend of the whole project), the following files are created:
  - **isnap/hints/example-display.js**

    -- *ExampleDisplay* is created for the display of example fetched from server based on the current code. The proccess of generating example based on the current code is implemented in the backend. A button labelled "Show Examples" is added to the navigation bar. When clicked, a POST xhr request will be sent to the server asking for the example.

    -- If the button is clicked with 'shift' key pressed, a hidden list will show up with option 'List of examples'. A *ExampleListDialogMorph* is defined in example-display.js to display a list of example fetched from the server. User can choose any example to view its content, while sending a POST xhr request to the backend. How this request will be used in the backend is not decided yet.

    -- An alternative design of *ExampleListDialogMorph* and a *ObjectiveListDialogMorph* are also available. They are not needed at the moment, therefore commented out. But they may be useful in the future.
  - **isnap/loaded-scripts-dialog-box-morph.js**

    -- *LoadedScriptsDialogBoxMorph* is created for the display of XML file of format
    <scripts><script>...</script><script>...</script></scripts>
    This custom morph will put two different ScriptMorphs into two horizontally parallel zones. Each script is runnable with buttons 'Run Script 1' and 'Run Script 2'.

The following files are updated:
  - **isnap/hints/hint-provider.js**

    -- *HintProvider.prototype.sendSelectedExample* is added to send data about selected example in the example list

    -- *HintProvider.prototype.getExamplesFromServer* is added to get the data of example list

    -- *HintProvider.prototype.processExample* is added to process data of example list for display in ExampleDisplay
  - **isnap/gui.js**

    -- *IDE_Morph.prototype.rawOpenScriptsString* and *IDE_Morph.prototype.openScriptsString* are added to accept drag and drop of XML files of format <scripts><script>…</script><script>…</script></scripts>

## SnapHints feature extension
For the SnapHints project (backend of the whole project), the following files are created:
  - **SnapHints/HintEvaluation/src/edu/isnap/eval/milestones/blockFilter.java**

    -- Wrote codes to generate XML based on the assignment attempts data from *Fall2016.Squiral*. Attempted to find ways of filtering assignment attempt rows based on 'First Appearance' and write filtered rows to CSV files.
  - **SnapHints/iSnap/src/edu/isnap/hint/util/NodeToXML.java**

    -- Wrote codes to transform Node defined in edu.isnap.node to XML format. The transformation was tested for node types *snapshot*, *stage*, *sprite*, *script*, *customBlock*, *varDec*, *evaluateCustomBlock*, *literal*, *varMenu*, *var* and *list*.

The following files are updated:
  - **SnapHints/HintServer/src/HintServlet.java**

    -- Added backend support for example display and example list

Feel free to reach out to me for questions about working on my code through email -  yrao3@ncsu.edu

Yudong RAO , April 28, 2019