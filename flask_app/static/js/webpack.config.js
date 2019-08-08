var path = require('path');
module.exports = {
    entry: "./dropDown.js",
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: "bundle.js",
        publicPath: '/dist'
    },
    module: {
        rules: [
            process.env.NODE_ENV === 'production' ? {
                test: /\.js$/,
                use: 'babel-loader'
            } : {},
            {
                test: /\.js$/,
                use: [
                    'ify-loader',
                    'transform-loader?plotly.js/tasks/compress_attributes.js',
                ]
            },
        ]
    }
};

