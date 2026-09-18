import AppKit

final class Launcher: NSObject, NSApplicationDelegate {
    var process: Process?
    var window: NSWindow!
    var status: NSTextField!
    var button: NSButton!
    var quitting = false
    var readerFolder: URL?

    func applicationDidFinishLaunching(_ notification: Notification) {
        let menu = NSMenu()
        let item = NSMenuItem()
        menu.addItem(item)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit Voice PubMed Reader", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = appMenu
        NSApp.mainMenu = menu
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 480, height: 210), styleMask: [.titled, .closable, .miniaturizable], backing: .buffered, defer: false)
        window.title = "Voice PubMed Reader"
        window.isReleasedWhenClosed = false
        let heading = NSTextField(labelWithString: "Voice PubMed Reader")
        heading.font = .boldSystemFont(ofSize: 22)
        heading.frame = NSRect(x: 24, y: 156, width: 430, height: 32)
        status = NSTextField(wrappingLabelWithString: "Opening the reader…")
        status.frame = NSRect(x: 24, y: 72, width: 430, height: 76)
        button = NSButton(title: "Start reader", target: self, action: #selector(startReader))
        button.frame = NSRect(x: 24, y: 22, width: 200, height: 36)
        button.bezelStyle = .rounded
        let quit = NSButton(title: "Quit reader", target: NSApp, action: #selector(NSApplication.terminate(_:)))
        quit.frame = NSRect(x: 250, y: 22, width: 200, height: 36)
        quit.bezelStyle = .rounded
        for view in [heading, status!, button!, quit] { window.contentView?.addSubview(view) }
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        startReader()
    }

    @objc func startReader() {
        guard process?.isRunning != true else { return }
        let fm = FileManager.default
        let saved = UserDefaults.standard.string(forKey: "ReaderFolder")
        let configured = Bundle.main.object(forInfoDictionaryKey: "ReaderFolder") as? String
        let normal = fm.homeDirectoryForCurrentUser.appendingPathComponent("Documents/voice_pubmed_bot").path
        let candidates = [saved, configured, normal].compactMap { $0 }
        let folder: URL
        if let found = candidates.first(where: { fm.fileExists(atPath: $0 + "/run_realtime_pubmed.command") }) {
            folder = URL(fileURLWithPath: found)
        } else {
            let picker = NSOpenPanel()
            picker.message = "Choose the installed voice_pubmed_bot folder. One-time setup is required on a new Mac."
            picker.canChooseDirectories = true
            picker.canChooseFiles = false
            guard picker.runModal() == .OK, let chosen = picker.url,
                  fm.fileExists(atPath: chosen.appendingPathComponent("run_realtime_pubmed.command").path) else {
                status.stringValue = "Reader folder not selected. Choose Start reader after installation."
                return
            }
            folder = chosen
        }
        readerFolder = folder
        UserDefaults.standard.set(folder.path, forKey: "ReaderFolder")
        let child = Process()
        child.executableURL = URL(fileURLWithPath: "/bin/bash")
        child.arguments = [folder.appendingPathComponent("run_realtime_pubmed.command").path]
        child.currentDirectoryURL = folder
        var environment = ProcessInfo.processInfo.environment
        let python = Bundle.main.object(forInfoDictionaryKey: "ReaderPython") as? String ?? "/usr/bin/python3"
        environment["PATH"] = folder.appendingPathComponent(".venv/bin").path + ":" + URL(fileURLWithPath: python).deletingLastPathComponent().path + ":/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        child.environment = environment
        // Do not persist transcripts, keys or diagnostic output in application logs.
        child.standardOutput = FileHandle.nullDevice
        child.standardError = FileHandle.nullDevice
        child.terminationHandler = { [weak self] completed in
            DispatchQueue.main.async {
                guard let self = self, !self.quitting else { return }
                self.button.isEnabled = true
                self.status.stringValue = "Reader stopped. Choose Start reader to retry. If it stops again, the reader installation or configuration needs attention."
                self.window.makeKeyAndOrderFront(nil)
            }
        }
        do {
            try child.run()
            process = child
            button.isEnabled = false
            status.stringValue = "The reader is opening in your browser. Press Enter there to start voice. Keep this app open while reading. Choose End session in the browser before Quit reader."
        } catch {
            status.stringValue = "Could not start the reader. Check its installation, then choose Start reader."
        }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        window.makeKeyAndOrderFront(nil)
        return true
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { return true }
    func applicationWillTerminate(_ notification: Notification) {
        quitting = true
        if process?.isRunning == true { process?.terminate() }
    }
}
let app = NSApplication.shared
let delegate = Launcher()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
