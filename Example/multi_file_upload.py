import asyncio
import time

import aiohttp

start_time = time.time()


async def download(download_function, drive_service, file_upload=None, gen_param=None, file_id=None):
    if gen_param is None:
        gen_param = [file_upload, True]
    else:
        file_upload = gen_param[0]
    file_metadata = {
        "name": file_upload,
    }
    media = MediaFileUploadGeneratorAsync(file_upload, download_function, resumable=True, gen_param=gen_param)
    file = (
        drive_service.service.files()
        .update(body=file_metadata, media_body=media, fields="id", fileId=file_id)
        .execute()
    )
    return file


def _gather_all(tasks, loop, session):
    gathered = asyncio.gather(*tasks, return_exceptions=True)
    loop.run_until_complete(gathered)
    results = []
    for task in tasks:
        try:
            results.append(task.result())
        except Exception as e:
            results.append(repr(e))
    loop.run_until_complete(session.close())
    return results


def download_multiple_files(loop, files, storage_supabase_file, drive_service, file_options=None):
    if file_options is None:
        file_options = {}
    session = aiohttp.ClientSession(headers=storage_supabase_file.headers)
    tasks = []
    for id_file in range(0, len(files), 2):
        task = asyncio.ensure_future(
            download(
                storage_supabase_file.download,
                drive_service,
                gen_param=[files[id_file], True, session],
                file_id=files[id_file + 1],
            )
        )

        tasks.append(task)
    return _gather_all(tasks, loop, session)


def upload_handle_multiple_files(loop, files_requests, files, storage_supabase_file, drive_service, file_options=None):
    if file_options is None:
        file_options = {}
    session = aiohttp.ClientSession(headers=storage_supabase_file.headers)
    tasks = []
    for id_file in range(0, len(files), 2):
        task = asyncio.ensure_future(
            storage_supabase_file.upload(
                files[id_file + 1],
                GDriveHandler.downloader,
                file_options,
                stream=True,
                param_gen=[files_requests[id_file], drive_service],
                session=session,
                content_type="form-data",
            )
        )

        tasks.append(task)
    return _gather_all(tasks, loop, session)
