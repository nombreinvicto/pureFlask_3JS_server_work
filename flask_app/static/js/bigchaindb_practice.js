const driver = require("bigchaindb-driver");
const db_url = "https://test.ipdb.io/api/v1/";

const conn = new driver.Connection(db_url);

// const alice = new driver.Ed25519Keypair();
// const bob = new driver.Ed25519Keypair();
//
// const assetdata = {
//     'car': {
//         'serial_number': 'abcd1234',
//         'manufacturer': 'NCState Dime Labs',
//     }
// };
//
// const metadata = {'planet': 'this is the DIME lab earth chodon'};
//
// const txCreateAliceSimple = driver.Transaction.makeCreateTransaction(
//     assetdata,
//     metadata,
//
//     // A transaction needs an output
//     [driver.Transaction.makeOutput(
//         driver.Transaction.makeEd25519Condition(alice.publicKey))
//     ],
//     alice.publicKey
// );
//
// txCreateAliceSimpleSigned =
// driver.Transaction.signTransaction(txCreateAliceSimple, alice.privateKey);
// txid = txCreateAliceSimpleSigned.id; console.log(txid);
// conn.postTransaction(txCreateAliceSimpleSigned);

conn.searchAssets('NCState DIME Labs CMaaS')
    .then((assets) => {
        console.log(assets);
    });


