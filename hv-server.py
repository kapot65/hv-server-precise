import asyncio
from asyncio import StreamReader, StreamWriter

import dfparser

from hardware_manager import INPUT, OUTPUT, routine


async def talk_to_client(reader: StreamReader, writer: StreamWriter):
    peername = writer.get_extra_info('peername')
    print(f'Connection from {peername}')

    subcription = asyncio.Queue()

    async def process_output():
        while True:
            # this can also await asyncio.sleep() or whatever is needed
            message = await subcription.get()
            meta = message['meta']
            data = message['data']

            print(meta, data)

            if meta['answer_type'] == 'get_voltage':
                print('here!')
                writer.write(dfparser.create_message(meta, data))
                await writer.drain()

    OUTPUT.subscriptions.add(subcription)
    output_coro = asyncio.create_task(process_output())

    buffer = b''

    while not writer.is_closing() and not reader.at_eof():
        buffer += await reader.read(1024)
        messages, buffer = dfparser.get_messages_from_stream(buffer)
        for message in messages:
            await INPUT.put(message)
    
    print(f'Connection from {peername} closed')
    output_coro.cancel()
    OUTPUT.subscriptions.remove(subcription)
        

if __name__ == "__main__":
    loop = asyncio.new_event_loop()

    routine_coro = loop.create_task(routine())

    coro = asyncio.start_server(talk_to_client, '0.0.0.0', 5555)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Programm stoped by user input")
        

    server.close()  
    loop.run_until_complete(server.wait_closed())
