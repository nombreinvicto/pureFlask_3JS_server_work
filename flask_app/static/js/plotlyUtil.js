let plotly = require("plotly.js");
let lcnc_status_url = "http://192.168.0.11:3296/lcn_xyz_status";
let setIntervalObject = "";
let dataStreamFlag = true;

// get all the buttons and elements
let renderOutput = document.getElementById("renderOutput");
let initiatePlotButton = document.getElementById("initiatePlot");
let toggleDataStreamButton = document.getElementById("toggleDataStream");

// attach listeners to buttons
initiatePlotButton.addEventListener("click", () => {
    
    clearInterval(setIntervalObject);
    plotly.purge("renderOutput");
    renderPlot();
    
});

toggleDataStreamButton.addEventListener("click", () => {
    if (dataStreamFlag) {
        extendTrace();
    } else {
        clearInterval(setIntervalObject);
    }
    dataStreamFlag = !dataStreamFlag;
});

// plotly initialisation
let init_data = [{
    x: [0],
    y: [0],
    z: [0],
    mode: 'markers',
    marker: {
        size: 5,
        line: {
            color: 'rgba(0, 0, 255, 1)',
            width: 0.5
        },
        opacity: 0.8
    },
    type: 'scatter3d'
}];

let layout = {
    margin: {
        l: 1,
        r: 1,
        b: 1,
        t: 1
    }
};

function renderPlot() {
    plotly.newPlot("renderOutput", init_data, layout);
}

function extendTrace() {
    setIntervalObject = setInterval(() => {
        
        plotly.extendTraces("renderOutput", {
            x: [[Math.random() * 10]],
            y: [[Math.random() * 10]],
            z: [[Math.random() * 10]]
        }, [0]).then((res) => {
            console.log("extended trace: ");
            console.log(res);
        });
    }, 1000);
    
}

