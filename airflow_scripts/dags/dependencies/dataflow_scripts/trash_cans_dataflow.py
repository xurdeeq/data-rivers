from __future__ import absolute_import

import argparse
import json
import logging
import os

import apache_beam as beam
import avro
import fastavro
import dataflow_utils

from apache_beam.io import ReadFromText
from apache_beam.io.avroio import WriteToAvro
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from avro import schema
from datetime import datetime

from dataflow_utils import clean_csv_int, clean_csv_string, generate_args, get_schema


class ConvertToDicts(beam.DoFn):
    def process(self, datum):
        container_id, receptacle_model_id, assignment_date, last_updated_date, group_name, address, city, state, \
        zip, neighborhood, dpw_division, council_district, ward, fire_zone = datum.split(',')

        return [{
            'container_id': clean_csv_int(container_id),
            'receptacle_model_id': clean_csv_int(receptacle_model_id),
            'assignment_date': clean_csv_string(assignment_date),
            'last_updated_date': clean_csv_string(last_updated_date),
            'group_name': clean_csv_string(group_name),
            'address': clean_csv_string(address),
            'city': clean_csv_string(city),
            'state': clean_csv_string(state),
            'zip': clean_csv_int(zip),
            'neighborhood': clean_csv_string(neighborhood),
            'dpw_division': clean_csv_int(dpw_division),
            'council_district': clean_csv_int(council_district),
            'ward': clean_csv_int(ward),
            'fire_zone': clean_csv_string(fire_zone)
        }]


def run(argv=None):
    dt = datetime.now()
    parser = argparse.ArgumentParser()

    parser.add_argument('--input',
                        dest='input',
                        default='gs://{}_trash_cans/{}/{}/{}_smart_trash_containers.csv'.format(os.environ['GCS_PREFIX'],
                                                                                                dt.strftime('%Y'),
                                                                                                dt.strftime('%m').lower(),
                                                                                                dt.strftime("%Y-%m-%d")),
                        help='Input file to process.')
    parser.add_argument('--avro_output',
                        dest='avro_output',
                        default='gs://{}_trash_cans/avro_output/{}/{}/{}/avro_output'.format(os.environ['GCS_PREFIX'],
                                                                                             dt.strftime('%Y'),
                                                                                             dt.strftime('%m').lower(),
                                                                                             dt.strftime("%Y-%m-%d")),
                        help='Output directory to write avro files.')

    known_args, pipeline_args = parser.parse_known_args(argv)

    #TODO: run on on-prem network when route is opened
    # Use runner=DataflowRunner to run in GCP environment, DirectRunner to run locally
    pipeline_args.extend(generate_args('trash-cans-dataflow',
                                       '{}_trash_cans'.format(os.environ['GCS_PREFIX']),
                                       'DirectRunner'))

    avro_schema = get_schema('smart_trash_cans')

    pipeline_options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=pipeline_options) as p:
        # Read the text file[pattern] into a PCollection.
        lines = p | ReadFromText(known_args.input, skip_header_lines=1)

        load = (
                lines
                | beam.ParDo(ConvertToDicts())
                | WriteToAvro(known_args.avro_output, schema=avro_schema, file_name_suffix='.avro', use_fastavro=True))


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
