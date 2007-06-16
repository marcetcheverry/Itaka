#import "MyObject.h"
#import "HTTPServer.h"

HTTPServer *server2; //check this method of passing server pointer

@implementation MyObject


-(void)awakeFromNib {
	[GrowlApplicationBridge setGrowlDelegate:self];
}

//register the application with growl using this method. Returns a dictioanry with the possible
// notifications

//need to define a test notification
#define SERVICE_NAME @"ItakaNotify"

-(NSDictionary *)registrationDictionaryForGrowl {
	NSArray *arrayOfNotifys = [NSArray arrayWithObjects:SERVICE_NAME, nil];
	
	return [NSDictionary dictionaryWithObjectsAndKeys:
		arrayOfNotifys, GROWL_NOTIFICATIONS_ALL,
		arrayOfNotifys, GROWL_NOTIFICATIONS_DEFAULT, nil];
}

- (IBAction)startServer:(id)sender
{
	if ([sender title] != @"Stop") { 
	
	NSImage * image = [NSImage imageNamed:@"process-stop.png"];        
	[sender setImage: image]; // didnt alloc dont need to realaese
	[sender setTitle:@"Stop"];
	[self runHttpd]; //should check that
	

	
	//[GrowlApplicationBridge description:@"Hi from growl" notificationName:@"HI"];
		
	
	
	
	} else {
		NSImage * image = [NSImage imageNamed:@"media-playback-start.png"];        
		[sender setImage: image]; // didnt alloc dont need to realaese
		[sender setTitle:@"Start"];
		[server2 stop]; //stops the server
		
	}
	
}

- (IBAction)stopServer:(id)sender
{
}

- (IBAction)takeScreenshot:(id)sender
{
}

-runHttpd {
	NSAutoreleasePool * pool = [[NSAutoreleasePool alloc] init];
	
    HTTPServer *server = [[HTTPServer alloc] init];
    [server setType:@"_http._tcp."];
    [server setName:@"Itaka HTTP Server"];
    [server setDocumentRoot:[NSURL fileURLWithPath:@"/tmp"]];
	
	server2 = server; //copy the pointer of server to the variable server2 to be able to use it when topping the server
	
	[server setPort:[[portButton title] intValue]]; // sets server port. Gets title from prefernces port NSPopupBUtton and makes it into an integer.	
	
	[server setDelegate:self]; // sets an instant of  Myobject as the delegate of httpserver
	
	NSError *startError = nil;
    if (![server start:&startError] ) {
        NSLog(@"Error starting server: %@", startError);
    } else {
        NSLog(@"Starting server on port %d", [server port]);
    }
	
	return 0;
    [pool release];
}    

- (void)HTTPConnection:(HTTPConnection *)conn didSendResponse:(HTTPServerRequest *)mess {
	NSLog (@"new response");
	
	
	NSLog(@"tag is%d", [[screenButton selectedItem] tag]);
	
	if ([[screenButton selectedItem] tag] == 1) {
		NSLog (@"WIndow mode selected");
		system("screencapture -iW /tmp/image.jpg");
	}
		
	if ([[screenButton selectedItem] tag] == 2) {
		NSLog (@"Full screen mode");
		system("screencapture /tmp/image.jpg");
	}
	
	if ([[screenButton selectedItem] tag] == 3) {
		NSLog (@"Interactive mode");
		system("screencapture -i /tmp/image.jpg");
	}
	// need to add screenshot image changing
	//connect in IB
}


// this is of course a delegate function from httpserver that is executed when a new connection arrives
// need to write a method that makes sense of hte connection (so far dats is in HEX, since i shows position in memory
// no use!)
- (void)HTTPServer:(HTTPServer *)serv didMakeNewConnection:(HTTPConnection *)conn { 
	NSLog(@"Got new connection from server %s, conection %s",serv, conn);
}



@end
