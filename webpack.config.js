const path = require('path');

module.exports = {
    mode: 'development',
    entry: './npm/index.js',
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, 'npm/dist'),
    },
};