/* MyObject */

#import <Cocoa/Cocoa.h>
#import <iLifeControls/NFIWindow.h>
#import <iLifeControls/NFHUDPopUpButton.h>

@interface MyObject : NSObject
{
    IBOutlet NFHUDPopUpButton *portButton;
    IBOutlet NSButton *startButton;
    IBOutlet NSTextField *textField;
    IBOutlet NFIWindow *window;
}
- (IBAction)startServer:(id)sender;
- (IBAction)stopServer:(id)sender;
- (IBAction)takeScreenshot:(id)sender;
@end
