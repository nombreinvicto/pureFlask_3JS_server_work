//// importing the required libraries
let THREE = require("./OrbitControls");
let plotly = require("plotly.js/dist/plotly");
const axios = require("axios");

// supply chain member addresses
let cncOwnerAddress = '0x7e18763C0dcBcFF6e9931aE2b5Ec3b06746A6EeB';
let consumerAddress = '0x97698Ae226bE1573c5940dE64F50D12919826e54';

// blockchain related imports
const Web3 = require("web3");
const ABI = require("./abi");
const driver = require("bigchaindb-driver");
const bdb_url = "https://test.ipdb.io/api/v1/";
const conn = new driver.Connection(bdb_url);
const bip39 = require("bip39");
let consumerOnBigchain = new driver.Ed25519Keypair(bip39.mnemonicToSeed(consumerAddress).slice(0, 32));

// getting supply chain adresses
const sc_abi = ABI.sc_abi;
const sc_address = ABI.sc_address;
let sc_contract = null;

// Instantiate and set Infura Rinkeby as provider
let network_url = "https://rinkeby.infura.io/v3/d176758e64fb47eb8ba5a1d58933bf9a";

// initiating metamask environment
if (window.ethereum) {
    console.log("Connecting to Metamask");
    window.web3 = new Web3(ethereum);
    
    // Request account access if needed
    ethereum.enable().then((res) => {
        alert("User granted access to Metamask");
    }).catch((err) => {
        alert("User denied access to account");
        console.log(err);
        return;
    });
    
    // creating a smart contract
    sc_contract = new web3.eth.Contract(sc_abi, sc_address);
    
} else {
    // set the provider you want from Web3.providers
    alert("Metamask Wallet not available. Page Load Aborted. Please" +
              " install Metamask Plugin or use Brave Browser.");
    return;
}

// set up all links for AJAX requests
let localhost = "http://f360app.ngrok.io";
const publicDirectoryUrl = localhost + "/public";
const cadMetaDataUrl = localhost + "/cadmeta/";
let fusionFlaskServerUrl = localhost + "/fusion360";
let fusionFlaskServerLCNCUrl = localhost + "/send_gcode_to_lcnc";
let currentF360DocUrl = localhost + "/currentOpenDoc";
let getF360DocHashUrl = localhost + "/get_current_file_hash";
let lcnc_status_url_default = "http://pocketncsim.ngrok.io/lcn_xyz_status";
let lcnc_status_url = document.getElementById("machine_ip").value;
//let lcnc_status_url = "http://152.1.58.35:3296/lcn_xyz_status";
let testBDBUrl = "https://test.ipdb.io/api/v1/assets/?search=";

//// 3.js initialisations
// camera, scene init
let scene, camera, renderer;
scene = new THREE.Scene();
scene.background = new THREE.Color(0x5fa1b3);
const aspectRatio = window.innerWidth / window.innerHeight;
camera = new THREE.PerspectiveCamera(45, aspectRatio, 0.1, 1000);
camera.position.z = 500;

// renderer init
renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth * (0.6),
                 window.innerHeight * (0.6));
let renderOutputElement = document.getElementById("renderOutput");
renderOutputElement.appendChild(renderer.domElement);

// OrbitalControl init
let controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.campingFactor = 0.25;
controls.enableZoom = true;

// set lighting directions
let createLighting = function () {
    
    let keyLight = new THREE.DirectionalLight(
        new THREE.Color('hsl(0,0%,100%)'), 1.0);
    keyLight.position.set(-100, 0, 100);
    let fillLight = new THREE.DirectionalLight(
        new THREE.Color('hsl(0,0%,100%)'), 0.75);
    fillLight.position.set(100, 0, 100);
    let backLight = new THREE.DirectionalLight(0xffffff, 1.0);
    backLight.position.set(100, 0, -100).normalize();
    let topLight = new THREE.DirectionalLight(
        new THREE.Color('hsl(0,0%,100%)'), 1.0);
    topLight.position.set(0, 1, 0);
    let bottomLight = new THREE.DirectionalLight(
        new THREE.Color('hsl(0,0%,100%)'), 1.0);
    //
    bottomLight.position.set(0, -1, 0);
    scene.add(keyLight);
    scene.add(fillLight);
    scene.add(backLight);
    scene.add(topLight);
    scene.add(bottomLight);
    
    // const color = 0xFFFFFF;
    // const intensity = 1;
    // const light = new THREE.AmbientLight(color, intensity);
    // scene.add(light);
    
};

// stl file drop down list initialisations
var ddownList = document.getElementById('selectSTL');
let panelNameElement = document.getElementById("panelName");
panelNameElement.innerHTML = "<b>Control Panel</b>";
let flaskServerResponsePanelName = document
    .getElementById("flaskServerResponsePanelName");
flaskServerResponsePanelName.innerHTML = "<b>Status Panel</b>";

// setting/getting up some of the initial HTML elements
let controlPanelForm = document.getElementById('controlPanel');

let fileList = null;
axios.get(publicDirectoryUrl).then((res) => {
    fileList = res.data;
    
    // populate the drop down list
    for (let file of fileList) {
        // populate with only stl files
        if (file.slice(file.length - 3, file.length) === 'stl') {
            let option = document.createElement('option');
            option.text = file;
            ddownList.add(option);
        }
    }
});

let flaskServerResponsePanel = document
    .getElementById('flaskServerResponse');
let currentF360DocPanel = document.getElementById('f360DocOpen');
let refreshF360DocButton = document.getElementById('refreshDoc');
refreshF360DocButton.addEventListener('click', () => {
    axios.get(currentF360DocUrl).then((res) => {
        currentF360DocPanel.innerText = res.data.toString();
    });
});
refreshF360DocButton.click();

// all plotly tasks//////////////////////////////////////////////////
// get all the buttons and elements
let setIntervalObject = "";
let renderOutput = document.getElementById("renderOutput");
let togglePlotButton = document.getElementById("togglePlot");
let togglePlotFlag = true;
let firsPlotFlag = true;
let refreshPlotButton = document.getElementById("refreshPlot");
let toggleDataStreamButton = document.getElementById("toggleDataStream");
let dataStreamFlag = true;
let globalDataTrace = "";
let globalPlotlyLayout = "";

let lcncStatusSpan = document.getElementById("lcncStatus");
let toggleDataStateSpan = document.getElementById("toggleDataStateDisplay");
let scanTestNetButton = document.getElementById("scan_testnet");

// attach listeners to buttons

//scan testnet
scanTestNetButton.addEventListener('click', () => {
    
    let bdb_testnet_tag = document.getElementById("bdb_tag").value;
    if (bdb_testnet_tag === "") {
        alert('scan requires non-null tag');
    } else {
        
        window.open(testBDBUrl + `{${bdb_testnet_tag}}`);
    }
});

togglePlotButton.addEventListener("click", () => {
    if (togglePlotFlag && firsPlotFlag) {
        renderNewPlot();
        firsPlotFlag = !firsPlotFlag;
    } else if (togglePlotFlag && !firsPlotFlag) {
        // if togglePlotFlag is true, but not firstPlot means render
        // previously running data trace of plotly
        renderPreviousPlot();
    } else {
        // if togglePlotflag is false means render 3JS DOM
        renderThreeJSDOM();
    }
    togglePlotFlag = !togglePlotFlag;
});

refreshPlotButton.addEventListener("click", () => {
    stopUpdatePlotlyChart();
    renderNewPlot();
});

toggleDataStreamButton.addEventListener("click", () => {
    if (dataStreamFlag) {
        
        lcnc_status_url = document.getElementById("machine_ip").value;
        if (lcnc_status_url !== "") {
            //lcnc_status_url = lcnc_status_url_default;
            // uncomment here to change from pocketnc to data stream simu
            updatePlotlyChart();
        } else {
            
            extendTrace();
        }
        
    } else {
        stopUpdatePlotlyChart();
    }
    dataStreamFlag = !dataStreamFlag;
});

function renderNewPlot() {
    renderOutput.innerHTML = "";
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
    globalDataTrace = init_data;
    globalPlotlyLayout = layout;
    plotly.newPlot("renderOutput", init_data, layout);
}

// render previous plot
function renderPreviousPlot() {
    renderOutput.innerHTML = "";
    plotly.newPlot("renderOutput", globalDataTrace, globalPlotlyLayout);
}

// this is for experimental update for the chart
function extendTrace() {
    toggleDataStateSpan.classList.add("greenDisplay");
    toggleDataStateSpan.classList.remove("redDisplay");
    toggleDataStateSpan.innerText = "STREAM ON";
    setIntervalObject = setInterval(() => {
        plotly.extendTraces("renderOutput", {
            x: [[Math.random() * 10]],
            y: [[Math.random() * 10]],
            z: [[Math.random() * 10]]
        }, [0]).then((res) => {
            console.log("extended trace: ");
            //console.log(res);
        });
    }, 1000);
}

// periodically request xyz data from LCNC and then update plot
function updatePlotlyChart() {
    toggleDataStateSpan.classList.add("greenDisplay");
    toggleDataStateSpan.classList.remove("redDisplay");
    toggleDataStateSpan.innerText = "STREAM ON";
    lcnc_status_url = document.getElementById("machine_ip").value;
    setIntervalObject = setInterval(function () {
        
        axios.get(lcnc_status_url).then((res) => {
            if (res.data["error"]) {
                lcncStatusSpan.innerText = res.data["error"].toString();
                return;
            } else {
                lcncStatusSpan.innerText = res.data["motion_status_name"];
            }
            
            if (parseInt(res.data["motion_status_name"]) !== 2) {
                plotly.extendTraces("renderOutput", {
                    x: [[parseFloat(res.data["x"])]],
                    y: [[parseFloat(res.data["y"])]],
                    z: [[parseFloat(res.data["z"])]]
                }, [0]);
                
            }
        });
    }, 100);
}

function stopUpdatePlotlyChart() {
    toggleDataStateSpan.classList.remove("greenDisplay");
    toggleDataStateSpan.classList.add("redDisplay");
    toggleDataStateSpan.innerText = "STREAM OFF";
    clearInterval(setIntervalObject);
}

function renderThreeJSDOM() {
    renderOutput.innerHTML = "";
    renderOutput.appendChild(renderer.domElement);
}

//////////////////////////////////////////////////////////////////////
//// initialising stl loader
let stlLoader = new THREE.STLLoader();
var clickCounter = 0;
ddownList.addEventListener('click', function () {
    renderThreeJSDOM();
    clickCounter++;
    // using clickcounter to stop reload on first drop down roll down
    if (ddownList.value !== "0" && clickCounter > 1) {
        // option value defaults to option text if not specified
        clickCounter = 0;
        stlLoader.load(localhost + "/get_stl_file/" + ddownList.value, async function (geometry) {
            let mat = new THREE.MeshLambertMaterial({
                                                        color: 0xC0C0C0
                                                    });
            let mesh = new THREE.Mesh(geometry, mat);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            
            // first remove already existing models from scene
            while (scene.children.length > 0) {
                scene.remove(scene.children[0]);
            }
            createLighting();
            scene.add(mesh);
            
            // first make sure the form element is empty
            controlPanelForm.innerHTML = "";
            
            // parse the stl json meta data to populate controls panel
            const cadJsonMetaData = (await axios.get(cadMetaDataUrl + ddownList.value)).data;
            
            // to show alphabetically ordered panels
            let dimArray = [];
            let cols = [];
            let tableRowElement = '';
            
            for (let dim in cadJsonMetaData) {
                dimArray.push(dim);
            }
            dimArray.sort();
            let dimArrayLength = dimArray.length;
            let dimArrayIterator = dimArray.entries();
            
            // change height of parent div acc to the number ofelements coming
            let parentDivElement = document.getElementById('parent_div');
            if (dimArrayLength > 2) {
                let rowNum = Math.round(dimArrayLength / 2);
                let totalHeight = 150 * rowNum + 155;
                parentDivElement.style.height = totalHeight.toString() + 'px';
            } else {
                parentDivElement.style.height = '300px';
            }
            
            // lets iterate over elements and populate control panel
            for (let dim of dimArray) {
                let currentDimIndex = dimArrayIterator.next().value[0];
                let labelForRangeControl = document.createElement('label');
                let rangeControlElement = document.createElement('input');
                let spanElement = document.createElement('span');
                
                console.log("CAD metadata:");
                console.log(cadJsonMetaData);
                
                // creating the range element
                rangeControlElement.type = "range";
                rangeControlElement.min = cadJsonMetaData[dim]["min"];
                rangeControlElement.max = cadJsonMetaData[dim]["max"];
                rangeControlElement.name = dim;
                rangeControlElement.id = dim;
                rangeControlElement.step = "0.05";
                rangeControlElement.setAttribute('value',
                                                 cadJsonMetaData[dim]["currentValue"]);
                
                labelForRangeControl.setAttribute('for', dim);
                labelForRangeControl.innerText = dim;
                
                // set attributes for the span element
                spanElement.setAttribute('id', 'spanFor' + dim);
                spanElement.innerText = rangeControlElement.value;
                
                // add all the elements to the DOM in the control
                // Panel
                let parElem1 = document.createElement("p");
                let parElem2 = document.createElement("p");
                let tableCellElement = document.createElement('td');
                
                parElem1.appendChild(labelForRangeControl);
                parElem2.append(rangeControlElement, spanElement);
                //controlPanelForm.append(parElem1, parElem2);
                tableCellElement.append(parElem1, parElem2);
                cols.push(tableCellElement);
                
                if (cols.length === 1) {
                    let spacerTd = document.createElement('td');
                    spacerTd.style.width = '10px';
                    cols.push(spacerTd);
                }
                
                if (((currentDimIndex === dimArrayLength - 1) && (dimArrayLength % 2 !== 0)) ||
                    cols.length === 3) {
                    tableRowElement = document.createElement('tr');
                    tableRowElement.append(...cols);
                    controlPanelForm.appendChild(tableRowElement);
                    cols = [];
                }
                
                //
                // connect rangeControlElement to onchange
                // listeners for display change on the numeric
                // outputs
                rangeControlElement.addEventListener('change', () => {
                    // get the corresponding span element
                    let spanElement =
                        document.getElementById('spanFor' + dim);
                    spanElement.innerText = rangeControlElement.value;
                });
            }
            
            // we need to also send the buttons to disable
            var buttonArray = [];
            var updateCADButton = document.createElement('button');
            var postToolpathButton = document.createElement('button');
            
            updateCADButton.type = "button";
            updateCADButton.innerText = "Update Model";
            updateCADButton.classList.add("submitButton");
            controlPanelForm.appendChild(updateCADButton);
            
            // now add button for gcode export
            postToolpathButton = document.createElement('button');
            let spanElement2 = document.createElement('span');
            postToolpathButton.type = 'button';
            postToolpathButton.innerText = "Send Make Order";
            postToolpathButton.classList.add("submitButton");
            //controlPanelForm.appendChild(spanElement2);
            controlPanelForm.appendChild(postToolpathButton);
            
            buttonArray.push(updateCADButton, postToolpathButton);
            
            // object and functional initialisations
            function disableButtons() {
                buttonArray.forEach((button) => {
                    button.disabled = true;
                });
            }
            
            function enableButtons() {
                buttonArray.forEach((button) => {
                    button.disabled = false;
                });
            }
            
            // attach an event listener to the submit button = Update CAD
            updateCADButton.addEventListener('click', () => {
                
                let allInputs = document.querySelectorAll('input');
                flaskServerResponsePanel.innerHTML = "";
                let flaskServerPostReqBody = {};
                allInputs.forEach((currentInput) => {
                    flaskServerPostReqBody[currentInput.id] = currentInput.value;
                });
                // also pass the filename
                flaskServerPostReqBody['filename'] = ddownList.value;
                console.log("this is the POST req body before" +
                                " param change");
                console.log(flaskServerPostReqBody);
                // disable buttons before sending request to do param change
                disableButtons();
                flaskServerResponsePanel.innerText = "Updating CAD model in remote server...";
                axios.post(fusionFlaskServerUrl, flaskServerPostReqBody).then((res) => {
                    flaskServerResponsePanel.innerText = res.data.toString();
                    clickCounter = 2;
                    ddownList.click();
                    setTimeout(() => {
                        flaskServerResponsePanel.innerText = "IDLE";
                        enableButtons();
                    }, 5000);
                });
            });
            
            postToolpathButton.addEventListener('click', () => {
                console.log("sending req to lcnc");
                disableButtons();
                // g code generation takes long time. so
                // making this ajax call asynchronous
                
                try {
                    // call smart contract function to intiate purchase order
                    sc_contract
                        .methods
                        .initiatePurchaseOrder("mahmud", "raleigh", 1, 2)
                        .send({from: consumerAddress})
                        .on("receipt", function (receipt) {
                            console.log(receipt);
                            let po = receipt.events.CreateQuoteForCustomer.returnValues[0];
                            let price = parseInt(receipt.events.CreateQuoteForCustomer.returnValues[1]);
                            price = price * 10;
                            
                            // hexify for smart contarct call
                            let po_bn = web3.utils.toHex(po);
                            let price_bn = web3.utils.toHex(price);
                            
                            // now call make order
                            sc_contract
                                .methods
                                .makeOrder(po_bn)
                                .send({
                                          from: consumerAddress,
                                          value: price_bn
                                      })
                                .on("receipt", async (receipt) => {
                                    console.log(receipt);
                                    
                                    // this is an async call to post the
                                    // toolpath
                                    flaskServerResponsePanel.innerText = "Posting new toolpath...";
                                    axios.get(fusionFlaskServerLCNCUrl).then((res) => {
                                        flaskServerResponsePanel.innerText = res.data.toString();
                                        setTimeout(() => {
                                            flaskServerResponsePanel.innerText = "IDLE";
                                            enableButtons();
                                        }, 5000);
                                    });
                                    
                                    // also send transaction to BigchainDB
                                    let asset = {};
                                    let partName = (await axios.get(currentF360DocUrl)).data;
                                    let partFileHash = (await axios.get(getF360DocHashUrl)).data;
                                    
                                    // set the asset name
                                    asset["ethereum_client"] = consumerAddress;
                                    asset['platform'] = "NCState DIME Labs CMaaS";
                                    asset['partName'] = partName;
                                    asset['part_STL_hash_md5'] = partFileHash;
                                    
                                    let metadata = {};
                                    for (let dim in cadJsonMetaData) {
                                        metadata[dim] = cadJsonMetaData[dim]["currentValue"];
                                    }
                                    asset['dimension_metadata'] = metadata;
                                    asset["timestamp"] = new Date().getTime().toString().slice(0, -3);
                                    const metadata_bdb = {
                                        'platform': 'NCState DIME Labs CMaaS'
                                    };
                                    
                                    // add a time stamp
                                    let dateObject = {};
                                    dateObject.day = new Date().getUTCDate();
                                    dateObject.month = new Date().getUTCMonth() + 1;
                                    dateObject.year = new Date().getUTCFullYear();
                                    asset["dateObject"] = dateObject;
                                    asset["description"] = "This is a" +
                                        " sample part made by the DIME labs" +
                                        " CMaaS platform";
                                    
                                    // lets create the BDB TX
                                    const txCreate = driver.Transaction.makeCreateTransaction(
                                        asset,
                                        metadata_bdb,
                                        
                                        // A transaction needs an output
                                        [driver.Transaction.makeOutput(
                                            driver.Transaction.makeEd25519Condition(consumerOnBigchain.publicKey))
                                        ],
                                        consumerOnBigchain.publicKey
                                    );
                                    
                                    //lets sign the Tx
                                    let txCreateSigned = driver.Transaction.signTransaction(txCreate, consumerOnBigchain.privateKey);
                                    
                                    // send the Tx
                                    conn.postTransaction(txCreateSigned);
                                    let bdb_message = "BDB Transaction Sent";
                                    console.log(bdb_message);
                                    alert(bdb_message);
                                    
                                });
                        });
                } catch (e) {
                    console.log(e);
                }
            });
        });
    }
});
let animate = function () {
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate); // recursively calls itself
};
animate();
