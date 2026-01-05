#define _GNU_SOURCE
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <threads.h>
#include <errno.h>
#include <stdint.h>

#include "ws/handshake.h"

// Could have to run $ gcc -std=c11 -o foo foo.c -lpthreads
#ifdef __STDC_NO_THREADS__
#error Threads required for program functionality
#endif

#define PORTNUMBER "28463"
#define MAXCONNECTIONS 128
#define MAXDIRECTORYSIZE 126
#define MAXREQUESTSIZE 1024
#define RELATIVEPATHTOVIDEOPATH "videos/"
#define VIDEOFILEEXTENSION ".vid"
#define DATABASELOCATION "../Website/webApp/database.db"

#define SEND(client,buf,len) send_all((client), (buf), (len), MSG_NOSIGNAL)

// Returns the new size of fileLocation
int videoIDToFileLocation(char* fileLocation, char* videoIDString, int videoIDStringSize){

    strcpy(fileLocation, RELATIVEPATHTOVIDEOPATH);
    strncat(fileLocation, videoIDString, videoIDStringSize);
    strcat(fileLocation, VIDEOFILEEXTENSION);

    return strlen(RELATIVEPATHTOVIDEOPATH) + strlen(videoIDString) + strlen(VIDEOFILEEXTENSION) + 1;
}

int sendWSframe(int socketDescriptor, char* data, uint64_t size){
    unsigned char* buffer = malloc(dataSize + 10);

    // Deal with arbitrary assignments
    buffer[0] = 0b10000001;
    buffer[1] = 0x03;

    // Copy the payload length into the buffer
	buffer[2] = (unsigned char)((size >> 56) & 255);
	buffer[3] = (unsigned char)((size >> 48) & 255);
	buffer[4] = (unsigned char)((size >> 40) & 255);
	buffer[5] = (unsigned char)((size >> 32) & 255);
	buffer[6] = (unsigned char)((size >> 24) & 255);
	buffer[7] = (unsigned char)((size >> 16) & 255);
	buffer[8] = (unsigned char)((size >> 8) & 255);
	buffer[9] = (unsigned char)((size & 255));

    // Copy the data into buffer
    
    buffer[2] = buffer[3] = buffer[4] = buffer[5] = 0;
    memcpy(buffer + 6, data, size);

    // Send data to client

    int dataToSend = size + 6;
    int dataSent;
    while ((dataSent = send(socketDescriptor, (void*)buffer, dataToSend, 0)) != size + 6){
        if(dataSent == -1){
            // An error has occured, return to main function, informing program
            return -1;
        } else{
            // Not all the data has been sent, attempt to send the rest of it

            dataToSend -= dataSent;
            buffer += dataSent;
        }
    }

    return dataSent;

}

int sendVideoData(void* socketDescriptorPointer){
    // Dereference and cast the pointer before free()ing to avoid any overwriting issues (although they shouldn't be possible as malloc is used on the pointer in the main thread)
    int socketDescriptor = *(int*)socketDescriptorPointer;

    free(socketDescriptorPointer);

    // Communicate with JavaScript using WebSocket API
    // WebSocket wrapping is assisted by code from https://github.com/Theldus/wsServer/
    // Deal with WebSocket Handshake
    char* handshakeRequest = malloc(MAXREQUESTSIZE);
    char* handshakeResponse;
    recv(socketDescriptor, (void*)handshakeRequest, MAXREQUESTSIZE, 0);

    get_handshake_response(handshakeRequest, &handshakeResponse);
    send(socketDescriptor, handshakeResponse, WS_HS_ACCLEN, 0);

    free(handshakeRequest); free(handshakeResponse);

    
    // Receive ID of video to send
    // Once again have to interpret stupid webSocket shit
    unsigned char* encodedVideoIDString = calloc(MAXDIRECTORYSIZE, 1);

    int encodedVideoIDStringSize = MAXDIRECTORYSIZE;

    if ((encodedVideoIDStringSize = recv(socketDescriptor, (void*)encodedVideoIDString, encodedVideoIDStringSize, 0)) <= 0){
        if (encodedVideoIDStringSize == 0 || encodedVideoIDStringSize == -1){
            // Either connection is closed, or an error has occured
            // In either case free all memory and return error

            free(encodedVideoIDString);
            return -1;
        }
    }

    // Interpret value of ID string according to webSocket standard
    // https://datatracker.ietf.org/doc/html/rfc6455
    char maskingKey[4];
    maskingKey[0] =  encodedVideoIDString[2];
    maskingKey[1] =  encodedVideoIDString[3];
    maskingKey[2] =  encodedVideoIDString[4];
    maskingKey[3] =  encodedVideoIDString[5];

    int videoIDStringSize = encodedVideoIDStringSize - 6;
    char* videoIDString = malloc(videoIDStringSize);
    for(int i = 0; i < videoIDStringSize; i++){
        videoIDString[i] = encodedVideoIDString[i + 6] ^ maskingKey[i % 4];
    }
    
    videoIDString = realloc(videoIDString, videoIDStringSize);

    // Now we have the actual videoID, use it to find the file location
    // Do some MySQL magic, and put the file location of the item in the VideoDirectory String
    char* fileLocation = malloc(MAXDIRECTORYSIZE);
    int fileLocLen = videoIDToFileLocation(fileLocation, videoIDString, videoIDStringSize);
    fileLocation = realloc(fileLocation, fileLocLen);


    // Open the file and send the data to the client machine
    FILE* fp = fopen(fileLocation, "rb");

    // Get metadata from file

    int16_t width;
    int16_t height;
    int8_t fps;
    int8_t time;

    fread(&width, sizeof(int16_t), 1, fp);
    fread(&height, sizeof(int16_t), 1, fp);
    fread(&fps, sizeof(int8_t), 1, fp);
    fread(&time, sizeof(int8_t), 1, fp);


    // Total number of bytes in file from this point is given by 3 * width * height * fps * time
    // Send this to client

    char* metaData = malloc(6);

    // Copy metaData into metaData buffer
    metaData[0] = (width >> 8); metaData[1] = (width << 8) >> 8;
    metaData[2] = (height >> 8); metaData[3] = (height << 8) >> 8;
    metaData[4] = fps;
    metaData[5] = time;

    sendWSframe(socketDescriptor, metaData, 6);
    free(metaData);

    // Iterate through the number of frames, sending a frame at a time
    
    char* buffer = malloc(3 * width * height);
    for(int i = 0; i < fps*time; i++){
        fread(buffer, 1, 3 * width * height, fp);

        // Send frame data in webSocket standard
        if (sendWSframe(socketDescriptor, buffer, 3 * width * height, 0) != 3 * width * height){
            // An error has occured, so free memory, shutdown connection and terminate thread 
            free(buffer);
            fclose(fp);
            shutdown(socketDescriptor, 2);

            return thrd_failure;
        }
        
    } free(buffer);
    
    fclose(fp);
    shutdown(socketDescriptor, 2);

    return thrd_success;
}

int main(int argc, char** argv){

    int status;
    // Socket File Descriptors. These basically act as "pointers" to the sockets
    // connectionSocketDescriptor need to be a pointer (actual pointer) so that it doesn't cause multithreading issues 
    int socketDescriptor, *connectionSocketDescriptorPointer;
    struct addrinfo hints, *connectionInfo;
    struct sockaddr_storage addressInfo; socklen_t addressLength = sizeof(addressInfo);
    int breakCondition = 1; // Actually a boolean 
    thrd_t tempThreadHolder;

    // Prepare hints struct to be passed to getaddrinfo
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = 0;
    hints.ai_flags = AI_PASSIVE;

    // Create linked list of struct addrinfo with information of connection options 
    if ((status = getaddrinfo(NULL, /*PORTNUMBER*/ argv[1], &hints, &connectionInfo)) != 0){
        // On error, as program has not yet setup, inform user and exit program
        fprintf(stderr, "getaddrinfo fail: %s\n", gai_strerror(status));
        exit(EXIT_FAILURE);
    }

    // Create socket descriptor to listen on later
    if ((socketDescriptor = socket(connectionInfo->ai_family, connectionInfo->ai_socktype, connectionInfo->ai_protocol)) == -1){
        // On error, as program has not yet setup, inform user and exit program
        fprintf(stderr, "socket fail: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }

    // Bind socket to specific port so that multithreading can occur
    if (bind(socketDescriptor, connectionInfo->ai_addr, connectionInfo->ai_addrlen) == -1){
        // On error, as program has not yet setup, inform user and exit program
        fprintf(stderr, "binding fail: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }

    // Define the maxiumum number of incoming connections and prepare the socket for accept()
    if (listen(socketDescriptor, MAXCONNECTIONS) == -1){
        // On error, as program has not yet setup, inform user and exit program
        fprintf(stderr, "socket fail: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }
    
    while (breakCondition == 1){
        // Keep accepting incoming connections until server shutdown

        // Allocate new memory to the FD so other threads don't have their pointers overwritten SHOULD BE FREE()-ED IN sendVideoData()
        connectionSocketDescriptorPointer = (int*)malloc(sizeof(int));

        // Accept an incoming connection so it can be forwarded to a new thread
        if (((*connectionSocketDescriptorPointer) = accept(socketDescriptor, (struct sockaddr*)&addressInfo, &addressLength)) == -1){
            fprintf(stderr, "accepting fail: %s\n", gai_strerror(status));
            
            // As we are in the main program loop, if an error occurs, we clean up the memory state, 
            // we clean memory and continue with loop. The client can attempt to reconnect if they wish
            free(connectionSocketDescriptorPointer);
            continue;
        }

        // Create new thread to deal with this connection and then detach the thread
        if (thrd_create(&tempThreadHolder, sendVideoData, connectionSocketDescriptorPointer) != thrd_success){
            // Prevent any potential memory leaks
            free(connectionSocketDescriptorPointer);
            continue;
        }
        thrd_detach(tempThreadHolder);
    }

    freeaddrinfo(connectionInfo);
    return 0;
}