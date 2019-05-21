let plotly = require("plotly.js");

let trace1 = {
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
};

let layout = {
    margin: {
        l: 1,
        r: 1,
        b: 1,
        t: 1
    }
};

let init_data = [trace1];

module.exports = {
    plotly,
    init_data,
    layout
};

