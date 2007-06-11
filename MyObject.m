#import "MyObject.h"

@implementation MyObject

- (IBAction)startServer:(id)sender
{
	if ([sender title] != @"Stop") { 
	
	NSImage * image = [NSImage imageNamed:@"process-stop.png"];        
	[sender setImage: image]; // didnt alloc dont need to realaese
	[sender setTitle:@"Stop"];
	
	} else {
		NSImage * image = [NSImage imageNamed:@"media-playback-start.png"];        
		[sender setImage: image]; // didnt alloc dont need to realaese
		[sender setTitle:@"Start"];
	}
	
}

- (IBAction)stopServer:(id)sender
{
}

- (IBAction)takeScreenshot:(id)sender
{
}

@end
