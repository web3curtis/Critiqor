const vscode = require('vscode');

function critiqorTerminal() {
  const existing = vscode.window.terminals.find((terminal) => terminal.name === 'Critiqor');
  return existing || vscode.window.createTerminal('Critiqor');
}

function run(command) {
  const terminal = critiqorTerminal();
  terminal.show();
  terminal.sendText(command, true);
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand('critiqor.configureAgent', () => run('critiqor agents')),
    vscode.commands.registerCommand('critiqor.finalize', () => run('critiqor finalize')),
    vscode.commands.registerCommand('critiqor.dashboard', () => run('critiqor dashboard')),
  );
}

function deactivate() {}

module.exports = {activate, deactivate};
