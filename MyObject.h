/* MyObject */

#import <Cocoa/Cocoa.h>
#import <iLifeControls/NFIWindow.h>
#import <iLifeControls/NFHUDPopUpButton.h>
#import <Growl/Growl.h> 
// growl framework

//@interface YourObjectController : NSObject <GrowlApplicationBridgeDelegate>

@interface MyObject : NSResponder <GrowlApplicationBridgeDelegate> //conforms to the growl object
{
    IBOutlet NFHUDPopUpButton *portButton; //contains the port to be used in the preferences pane
	IBOutlet NFHUDPopUpButton *screenButton; // preferences of full screen, window, etc
    IBOutlet NSButton *startButton;
    IBOutlet NSTextField *textField;
    IBOutlet NFIWindow *window;
}
- (IBAction)startServer:(id)sender;
- (IBAction)stopServer:(id)sender;
- (IBAction)takeScreenshot:(id)sender;

- (NSDictionary *) registrationDictionaryForGrowl;
@end
