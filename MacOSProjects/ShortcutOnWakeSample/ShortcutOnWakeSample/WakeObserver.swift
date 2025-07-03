//
//  WakeObserver.swift
//  ShortcutOnWakeSample
//
//  Created by Akshay Yadav on 5/29/25.
//

import Cocoa


class WakeObserver {
    init() {
        NSWorkspace.shared.notificationCenter.addObserver(
            self,
            selector: #selector(systemDidWake),
            name: NSWorkspace.didWakeNotification,
            object: nil
        )
    }

    @objc func systemDidWake(notification: Notification) {
        print("System just woke up!")
        if let url = URL(string: "shortcuts://run-shortcut?name=Turn%20On%20Desk%20Lamp") {
            NSWorkspace.shared.open(url)
        }
        // Place your custom code here
    }
}
